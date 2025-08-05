"""
Commerce models: Leads, Quotes, Orders, Shipping
"""
from django.db import models
from django.core.validators import MinValueValidator
from django_fsm import FSMField, transition
from decimal import Decimal
import uuid


class SalesLeadStatus(models.TextChoices):
    NO_LEAD = 'no_lead', 'No Lead'
    NEW = 'new', 'New'
    CONVERTED = 'converted', 'Converted'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    FORWARDED = 'forwarded', 'Forwarded'
    SENT_TO_DISTRIBUTOR = 'sent_to_distributor', 'Sent to Distributor'
    ACCEPTED_BY_DISTRIBUTOR = 'accepted_by_distributor', 'Accepted by Distributor'
    REJECTED_BY_DISTRIBUTOR = 'rejected_by_distributor', 'Rejected by Distributor'


class QuoteStatus(models.TextChoices):
    NO_REQUEST = 'no_request', 'No Request'
    NEW = 'new', 'New'
    REQUESTED = 'requested', 'Requested'
    RESPONDED = 'responded', 'Responded'
    ACCEPTED = 'accepted', 'Accepted'
    CANCELLED = 'cancelled', 'Cancelled'
    DECLINED = 'declined', 'Declined'
    PENDING = 'pending', 'Pending'
    PENDING_ACTIVATION = 'pending_activation', 'Pending Activation'


class OrderStatus(models.TextChoices):
    NO_ORDER = 'no_order', 'No Order'
    NEW = 'new', 'New'
    ACCEPTED = 'accepted', 'Accepted'
    IN_PROGRESS = 'in_progress', 'In Progress'
    INVOICED = 'invoiced', 'Invoiced'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'
    PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    DECLINED = 'declined', 'Declined'
    BACK_ORDERED = 'back_ordered', 'Back Ordered'


class Lead(models.Model):
    """Sales lead from buyer"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='leads')
    buyer_first_name = models.CharField(max_length=100)
    buyer_last_name = models.CharField(max_length=100)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=50, blank=True, null=True)
    buyer_company_name = models.CharField(max_length=255, blank=True, null=True)
    status = FSMField(default=SalesLeadStatus.NO_LEAD, choices=SalesLeadStatus.choices, protected=True)
    parent_lead = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                                   related_name='child_leads')
    source = models.CharField(max_length=50, default='web')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lead'
        ordering = ['-created_at']

    def __str__(self):
        return f"Lead {self.id} - {self.buyer_company_name or self.buyer_email}"

    @transition(field=status, source=SalesLeadStatus.NO_LEAD, target=SalesLeadStatus.NEW)
    def create(self):
        """Create new lead"""
        pass

    @transition(field=status, source=SalesLeadStatus.NEW, target=SalesLeadStatus.CONVERTED)
    def convert(self):
        """Convert lead to quote"""
        pass

    @transition(field=status, source=SalesLeadStatus.NEW, target=SalesLeadStatus.FORWARDED)
    def forward_to_distributor(self):
        """Forward lead to distributor"""
        pass

    @transition(field=status, source=SalesLeadStatus.NEW, target=SalesLeadStatus.SENT_TO_DISTRIBUTOR)
    def send_to_distributor(self):
        """Send lead to distributor"""
        pass

    @transition(field=status, source=SalesLeadStatus.SENT_TO_DISTRIBUTOR, target=SalesLeadStatus.ACCEPTED_BY_DISTRIBUTOR)
    def accept_by_distributor(self):
        """Distributor accepts lead"""
        pass

    @transition(field=status, source=SalesLeadStatus.SENT_TO_DISTRIBUTOR, target=SalesLeadStatus.REJECTED_BY_DISTRIBUTOR)
    def reject_by_distributor(self):
        """Distributor rejects lead"""
        pass


class DeliveryTerm(models.Model):
    """Delivery terms (FOB, CIF, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delivery_term'
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentTerm(models.Model):
    """Payment terms (Net 30, Net 60, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_term'
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentMode(models.Model):
    """Payment modes (Credit Card, Wire Transfer, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_mode'
        ordering = ['name']

    def __str__(self):
        return self.name


class PriceTier(models.Model):
    """Volume-based pricing tiers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='price_tiers_seller')
    buyer = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='price_tiers_buyer')
    destination = models.ForeignKey('tenants.TenantAddress', on_delete=models.CASCADE, related_name='price_tiers')
    product_sku = models.ForeignKey('products.ProductSKU', on_delete=models.CASCADE, related_name='price_tiers')
    delivery_term = models.ForeignKey(DeliveryTerm, on_delete=models.SET_NULL, blank=True, null=True)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, blank=True, null=True)
    minimum_uom_quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                              validators=[MinValueValidator(Decimal('0.01'))])
    price_per_uom = models.DecimalField(max_digits=10, decimal_places=2,
                                       validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    valid_from_date = models.DateTimeField(blank=True, null=True)
    valid_to_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'price_tier'
        ordering = ['seller', 'buyer', 'minimum_uom_quantity']

    def __str__(self):
        return f"{self.product_sku.number} - {self.price_per_uom} {self.currency} (min: {self.minimum_uom_quantity})"

    @staticmethod
    def get_current_price(quantity, price_tiers):
        """Get best price for given quantity from price tiers"""
        from django.utils import timezone
        now = timezone.now()
        
        applicable_tiers = [
            tier for tier in price_tiers
            if tier.is_active
            and quantity >= tier.minimum_uom_quantity
            and (tier.valid_from_date is None or tier.valid_from_date <= now)
            and (tier.valid_to_date is None or tier.valid_to_date >= now)
        ]
        
        if not applicable_tiers:
            return None
        
        # Return tier with lowest price
        best_tier = min(applicable_tiers, key=lambda t: t.price_per_uom)
        return best_tier.price_per_uom


class QuoteRequest(models.Model):
    """Quote request for price negotiation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='quote_requests_buyer')
    seller = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='quote_requests_seller')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, blank=True, null=True, related_name='quote_requests')
    number = models.CharField(max_length=50, unique=True)
    status = FSMField(default=QuoteStatus.NO_REQUEST, choices=QuoteStatus.choices, protected=True)
    warehouse = models.ForeignKey('tenants.TenantAddress', on_delete=models.PROTECT, related_name='quote_requests')
    delivery_term = models.ForeignKey(DeliveryTerm, on_delete=models.PROTECT)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.PROTECT)
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.PROTECT)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                        validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quote_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote {self.number} - {self.buyer.name} → {self.seller.name}"

    @transition(field=status, source=QuoteStatus.NO_REQUEST, target=QuoteStatus.NEW)
    def create_quote(self):
        """Create new quote"""
        self.is_active = True

    @transition(field=status, source=QuoteStatus.NEW, target=QuoteStatus.REQUESTED)
    def buyer_requests(self):
        """Buyer submits quote request"""
        pass

    @transition(field=status, source=[QuoteStatus.REQUESTED, QuoteStatus.PENDING], target=QuoteStatus.RESPONDED)
    def seller_responds(self):
        """Seller responds with pricing"""
        pass

    @transition(field=status, source=QuoteStatus.RESPONDED, target=QuoteStatus.REQUESTED)
    def seller_modifies(self):
        """Seller modifies quote (re-negotiation)"""
        pass

    @transition(field=status, source=QuoteStatus.RESPONDED, target=QuoteStatus.REQUESTED)
    def buyer_responds(self):
        """Buyer requests modification"""
        pass

    @transition(field=status, source=QuoteStatus.RESPONDED, target=QuoteStatus.ACCEPTED)
    def buyer_accepts(self):
        """Buyer accepts quote - creates purchase order"""
        self.is_active = False
        # Create purchase order will be handled in view/signal

    @transition(field=status, source=[QuoteStatus.NEW, QuoteStatus.REQUESTED, QuoteStatus.RESPONDED],
                target=QuoteStatus.CANCELLED)
    def cancel(self):
        """Cancel quote"""
        self.is_active = False

    @transition(field=status, source=[QuoteStatus.REQUESTED, QuoteStatus.PENDING], target=QuoteStatus.DECLINED)
    def seller_declines(self):
        """Seller declines quote"""
        self.is_active = False

    @property
    def subtotal(self):
        """Calculate subtotal from items"""
        return sum(item.total_value for item in self.items.all() if item.total_value)

    @property
    def total(self):
        """Calculate total including shipping"""
        return self.subtotal + self.shipping_cost


class QuoteRequestDetail(models.Model):
    """Line items in quote request"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    sku = models.ForeignKey('products.ProductSKU', on_delete=models.PROTECT, blank=True, null=True)
    requested_sku = models.ForeignKey('products.ProductSKU', on_delete=models.SET_NULL,
                                     blank=True, null=True, related_name='requested_quote_details')
    no_of_units = models.DecimalField(max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.01'))])
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))],
                                        blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quote_request_detail'
        ordering = ['quote_request', 'created_at']

    def __str__(self):
        return f"{self.quote_request.number} - {self.product.name}"

    @property
    def total_value(self):
        """Calculate total value for this line item"""
        if self.price_per_unit:
            return self.total_quantity * self.price_per_unit
        return Decimal('0.00')

    def get_price_from_tier(self):
        """Get price from price tier if available"""
        if not self.sku or not self.quote_request:
            return None
        
        price_tiers = PriceTier.objects.filter(
            seller=self.quote_request.seller,
            buyer=self.quote_request.buyer,
            destination=self.quote_request.warehouse,
            product_sku=self.sku,
            currency=self.currency,
        )
        
        if self.quote_request.delivery_term:
            price_tiers = price_tiers.filter(
                models.Q(delivery_term=self.quote_request.delivery_term) | models.Q(delivery_term__isnull=True)
            )
        
        if self.quote_request.payment_term:
            price_tiers = price_tiers.filter(
                models.Q(payment_term=self.quote_request.payment_term) | models.Q(payment_term__isnull=True)
            )
        
        return PriceTier.get_current_price(self.total_quantity, list(price_tiers))


class PurchaseOrder(models.Model):
    """Purchase order (confirmed order)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='purchase_orders_buyer')
    seller = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='purchase_orders_seller')
    quote_request = models.OneToOneField(QuoteRequest, on_delete=models.SET_NULL,
                                        blank=True, null=True, related_name='purchase_order')
    number = models.CharField(max_length=50, unique=True)
    status = FSMField(default=OrderStatus.NO_ORDER, choices=OrderStatus.choices, protected=True)
    warehouse = models.ForeignKey('tenants.TenantAddress', on_delete=models.PROTECT, related_name='purchase_orders')
    delivery_term = models.ForeignKey(DeliveryTerm, on_delete=models.PROTECT)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.PROTECT)
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.PROTECT)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                       validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"PO {self.number} - {self.buyer.name} → {self.seller.name}"

    @transition(field=status, source=OrderStatus.NO_ORDER, target=OrderStatus.NEW)
    def create_order(self):
        """Create new order"""
        pass

    @transition(field=status, source=OrderStatus.NEW, target=OrderStatus.ACCEPTED)
    def accept(self):
        """Seller accepts order"""
        pass

    @transition(field=status, source=OrderStatus.ACCEPTED, target=OrderStatus.IN_PROGRESS)
    def make_in_progress(self):
        """Start processing order"""
        pass

    @transition(field=status, source=[OrderStatus.ACCEPTED, OrderStatus.IN_PROGRESS], target=OrderStatus.INVOICED)
    def invoice(self):
        """Generate invoice"""
        pass

    @transition(field=status, source=[OrderStatus.ACCEPTED, OrderStatus.IN_PROGRESS, OrderStatus.INVOICED],
                target=OrderStatus.SHIPPED)
    def ship_order(self):
        """Ship order"""
        pass

    @transition(field=status, source=[OrderStatus.INVOICED, OrderStatus.SHIPPED], target=OrderStatus.PAYMENT_RECEIVED)
    def receive_payment(self):
        """Receive payment"""
        pass

    @transition(field=status, source=[OrderStatus.INVOICED, OrderStatus.SHIPPED, OrderStatus.PAYMENT_RECEIVED],
                target=OrderStatus.COMPLETED)
    def complete(self):
        """Complete order"""
        pass

    @transition(field=status, source=[OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.IN_PROGRESS],
                target=OrderStatus.CANCELLED)
    def cancel(self):
        """Cancel order"""
        self.is_active = False

    @property
    def subtotal(self):
        """Calculate subtotal from items"""
        return sum(item.total_value for item in self.items.all() if item.total_value)

    @property
    def total(self):
        """Calculate total including shipping"""
        return self.subtotal + self.shipping_cost


class PurchaseOrderDetail(models.Model):
    """Line items in purchase order"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    sku = models.ForeignKey('products.ProductSKU', on_delete=models.PROTECT)
    no_of_units = models.DecimalField(max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.01'))])
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_order_detail'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.order.number} - {self.product.name}"

    @property
    def total_value(self):
        """Calculate total value for this line item"""
        return self.total_quantity * self.price_per_unit


class ShipmentAdvice(models.Model):
    """Shipping information and tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='shipments')
    estimated_time_of_dispatch = models.DateTimeField(blank=True, null=True)
    estimated_time_of_arrival = models.DateTimeField(blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    carrier_number = models.CharField(max_length=100, blank=True, null=True)
    vessel_name = models.CharField(max_length=100, blank=True, null=True)
    port_of_loading = models.CharField(max_length=100, blank=True, null=True)
    port_of_discharge = models.CharField(max_length=100, blank=True, null=True)
    additional_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipment_advice'
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment for {self.order.number}"
