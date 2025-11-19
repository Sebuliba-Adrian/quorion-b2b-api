"""
Marketplace-specific commerce models
Includes notifications, payments, direct checkout, etc.
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class NotificationType(models.TextChoices):
    """Notification types"""

    ORDER_PLACED = "order_placed", "Order Placed"
    ORDER_ACCEPTED = "order_accepted", "Order Accepted"
    ORDER_SHIPPED = "order_shipped", "Order Shipped"
    ORDER_DELIVERED = "order_delivered", "Order Delivered"
    PAYMENT_RECEIVED = "payment_received", "Payment Received"
    REVIEW_POSTED = "review_posted", "Review Posted"
    PRODUCT_BACK_IN_STOCK = "product_back_in_stock", "Product Back in Stock"
    PRICE_DROP = "price_drop", "Price Drop"
    NEW_MESSAGE = "new_message", "New Message"
    QUOTE_RECEIVED = "quote_received", "Quote Received"
    QUOTE_ACCEPTED = "quote_accepted", "Quote Accepted"


class Notification(models.Model):
    """User notifications"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True, help_text="Link to related resource")
    data = models.JSONField(default=dict, blank=True, help_text="Additional notification data")
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    is_sms_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient.name} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=["is_read"])


class PaymentMethod(models.TextChoices):
    """Payment methods"""

    CREDIT_CARD = "credit_card", "Credit Card"
    DEBIT_CARD = "debit_card", "Debit Card"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    PAYPAL = "paypal", "PayPal"
    STRIPE = "stripe", "Stripe"
    CASH_ON_DELIVERY = "cash_on_delivery", "Cash on Delivery"
    NET_TERMS = "net_terms", "Net Terms"


class PaymentStatus(models.TextChoices):
    """Payment status"""

    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"
    CANCELLED = "cancelled", "Cancelled"


class Payment(models.Model):
    """Payment transactions"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey("commerce.PurchaseOrder", on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="External payment gateway ID")
    payment_gateway = models.CharField(max_length=50, blank=True, null=True, help_text="Stripe, PayPal, etc")
    gateway_response = models.JSONField(default=dict, blank=True, help_text="Payment gateway response")
    notes = models.TextField(blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["transaction_id"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} - {self.status}"


class DirectCheckout(models.Model):
    """Direct checkout session (bypass quote negotiation)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey("commerce.Cart", on_delete=models.CASCADE, related_name="checkouts")
    buyer = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="checkouts")
    shipping_address = models.ForeignKey(
        "tenants.TenantAddress", on_delete=models.PROTECT, related_name="shipping_checkouts"
    )
    billing_address = models.ForeignKey(
        "tenants.TenantAddress", on_delete=models.PROTECT, related_name="billing_checkouts"
    )
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices)
    delivery_term = models.ForeignKey("commerce.DeliveryTerm", on_delete=models.PROTECT)
    payment_term = models.ForeignKey("commerce.PaymentTerm", on_delete=models.PROTECT, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="USD")
    notes = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    order = models.ForeignKey(
        "commerce.PurchaseOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="direct_checkouts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "direct_checkout"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["buyer", "is_completed"]),
        ]

    def __str__(self):
        return f"Checkout {self.id} - {self.buyer.name} - {self.total_amount} {self.currency}"

    def calculate_totals(self):
        """Calculate checkout totals"""
        from commerce.models import Cart

        cart = Cart.objects.prefetch_related("items").get(id=self.cart_id)
        self.subtotal = cart.subtotal
        # Tax and shipping would be calculated based on business logic
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        self.save()


class ProductView(models.Model):
    """Track product views for analytics"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="product_views")
    viewer = models.ForeignKey(
        "tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="product_views"
    )
    session_id = models.CharField(max_length=255, blank=True, null=True, help_text="Anonymous session ID")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    referrer = models.CharField(max_length=500, blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_view"
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(fields=["product", "viewed_at"]),
            models.Index(fields=["viewer"]),
        ]

    def __str__(self):
        viewer_name = self.viewer.name if self.viewer else "Anonymous"
        return f"{self.product.name} viewed by {viewer_name}"


class SearchQuery(models.Model):
    """Track search queries for analytics and recommendations"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.CharField(max_length=255)
    searcher = models.ForeignKey(
        "tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="search_queries"
    )
    session_id = models.CharField(max_length=255, blank=True, null=True)
    results_count = models.IntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_query"
        ordering = ["-searched_at"]
        indexes = [
            models.Index(fields=["query"]),
            models.Index(fields=["searched_at"]),
        ]

    def __str__(self):
        return f"Search: {self.query} ({self.results_count} results)"


class PromoCode(models.Model):
    """Promotional discount codes"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(
        max_length=20, choices=[("percentage", "Percentage"), ("fixed", "Fixed Amount")], default="percentage"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    min_purchase_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0"))]
    )
    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount amount for percentage discounts",
    )
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Total usage limit (null = unlimited)")
    usage_count = models.IntegerField(default=0)
    per_user_limit = models.IntegerField(null=True, blank=True, help_text="Per-user usage limit")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "promo_code"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ' ' + 'USD'}"

    def is_valid(self):
        """Check if promo code is currently valid"""
        from django.utils import timezone

        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True

    def calculate_discount(self, amount):
        """Calculate discount amount for given purchase amount"""
        if not self.is_valid():
            return Decimal("0.00")
        if amount < self.min_purchase_amount:
            return Decimal("0.00")

        if self.discount_type == "percentage":
            discount = amount * (self.discount_value / Decimal("100"))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        else:  # fixed
            return min(self.discount_value, amount)
