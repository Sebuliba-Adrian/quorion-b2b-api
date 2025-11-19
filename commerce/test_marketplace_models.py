"""
Tests for marketplace commerce models
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from commerce.marketplace_models import (
    DirectCheckout,
    Notification,
    Payment,
    ProductView,
    PromoCode,
    SearchQuery,
)
from commerce.models import Cart, DeliveryTerm, PaymentMode, PaymentTerm, PurchaseOrder
from products.models import Product
from tenants.models import Tenant, TenantAddress


@pytest.fixture
def seller_tenant(db):
    """Create a seller tenant"""
    return Tenant.objects.create(name="Test Seller", type="seller", email="seller@test.com")


@pytest.fixture
def buyer_tenant(db):
    """Create a buyer tenant"""
    return Tenant.objects.create(name="Test Buyer", type="buyer", email="buyer@test.com")


@pytest.fixture
def product(db, seller_tenant):
    """Create a product"""
    return Product.objects.create(seller=seller_tenant, name="Test Product", description="Test description")


@pytest.fixture
def cart(db, buyer_tenant):
    """Create a cart"""
    return Cart.objects.create(buyer=buyer_tenant)


@pytest.fixture
def shipping_address(db, buyer_tenant):
    """Create a shipping address"""
    return TenantAddress.objects.create(
        tenant=buyer_tenant,
        address1="123 Main St",
        city="Test City",
        state="Test State",
        zip_code="12345",
        country="US",
        address_type="shipping",
    )


@pytest.fixture
def delivery_term(db):
    """Create a delivery term"""
    return DeliveryTerm.objects.create(name="Standard Shipping")


@pytest.fixture
def payment_term(db):
    """Create a payment term"""
    return PaymentTerm.objects.create(name="Net 30")


@pytest.fixture
def payment_mode(db):
    """Create a payment mode"""
    return PaymentMode.objects.create(name="Credit Card")


@pytest.fixture
def order(db, buyer_tenant, seller_tenant, shipping_address, delivery_term, payment_term, payment_mode):
    """Create a purchase order"""
    return PurchaseOrder.objects.create(
        buyer=buyer_tenant,
        seller=seller_tenant,
        warehouse=shipping_address,
        delivery_term=delivery_term,
        payment_term=payment_term,
        payment_mode=payment_mode,
    )


@pytest.mark.django_db
class TestNotification:
    """Tests for Notification model"""

    def test_notification_creation(self, buyer_tenant):
        """Test notification creation"""
        notification = Notification.objects.create(
            recipient=buyer_tenant,
            notification_type="order_update",
            title="Order Shipped",
            message="Your order has been shipped",
        )
        assert notification.recipient == buyer_tenant
        assert notification.notification_type == "order_update"
        assert notification.is_read is False

    def test_notification_mark_as_read(self, buyer_tenant):
        """Test mark_as_read method"""
        notification = Notification.objects.create(
            recipient=buyer_tenant, notification_type="general", title="Test", message="Test message"
        )
        assert notification.is_read is False

        notification.mark_as_read()
        assert notification.is_read is True


@pytest.mark.django_db
class TestPayment:
    """Tests for Payment model"""

    def test_payment_creation(self, order):
        """Test payment creation"""
        payment = Payment.objects.create(
            order=order, payment_method="credit_card", amount=Decimal("100.00"), currency="USD", status="pending"
        )
        assert payment.order == order
        assert payment.amount == Decimal("100.00")
        assert payment.status == "pending"

    def test_payment_string_representation(self, order):
        """Test payment __str__ method"""
        payment = Payment.objects.create(
            order=order, payment_method="credit_card", amount=Decimal("100.00"), status="pending"
        )
        assert "100.00" in str(payment)
        assert "pending" in str(payment)


@pytest.mark.django_db
class TestDirectCheckout:
    """Tests for DirectCheckout model"""

    def test_checkout_creation(self, cart, buyer_tenant, shipping_address, delivery_term, payment_term):
        """Test checkout creation"""
        checkout = DirectCheckout.objects.create(
            cart=cart,
            buyer=buyer_tenant,
            shipping_address=shipping_address,
            billing_address=shipping_address,
            payment_method="credit_card",
            delivery_term=delivery_term,
            payment_term=payment_term,
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("8.00"),
            shipping_cost=Decimal("10.00"),
            total_amount=Decimal("118.00"),
        )
        assert checkout.cart == cart
        assert checkout.buyer == buyer_tenant
        assert checkout.total_amount == Decimal("118.00")
        assert checkout.is_completed is False

    def test_checkout_calculate_totals(
        self, cart, buyer_tenant, shipping_address, delivery_term, payment_term, product
    ):
        """Test calculate_totals method"""
        # Add items to cart so cart.subtotal returns a value
        from commerce.models import CartItem

        CartItem.objects.create(cart=cart, product=product, quantity=Decimal("2.00"), unit_price=Decimal("50.00"))

        checkout = DirectCheckout.objects.create(
            cart=cart,
            buyer=buyer_tenant,
            shipping_address=shipping_address,
            billing_address=shipping_address,
            payment_method="credit_card",
            delivery_term=delivery_term,
            payment_term=payment_term,
            subtotal=Decimal("0.00"),  # Will be calculated from cart
            tax_amount=Decimal("8.00"),
            shipping_cost=Decimal("10.00"),
            discount_amount=Decimal("5.00"),
        )

        checkout.calculate_totals()
        # cart.subtotal = 100 (2 * 50), then: 100 + 8 + 10 - 5 = 113
        assert checkout.total_amount == Decimal("113.00")


@pytest.mark.django_db
class TestProductView:
    """Tests for ProductView model"""

    def test_product_view_creation(self, product, buyer_tenant):
        """Test product view creation"""
        view = ProductView.objects.create(product=product, viewer=buyer_tenant, ip_address="192.168.1.1")
        assert view.product == product
        assert view.viewer == buyer_tenant
        assert view.ip_address == "192.168.1.1"

    def test_anonymous_product_view(self, product):
        """Test anonymous product view (no viewer)"""
        view = ProductView.objects.create(product=product, ip_address="192.168.1.1")
        assert view.product == product
        assert view.viewer is None


@pytest.mark.django_db
class TestSearchQuery:
    """Tests for SearchQuery model"""

    def test_search_query_creation(self, buyer_tenant):
        """Test search query creation"""
        query = SearchQuery.objects.create(query="laptop", searcher=buyer_tenant, results_count=25)
        assert query.query == "laptop"
        assert query.searcher == buyer_tenant
        assert query.results_count == 25

    def test_anonymous_search_query(self):
        """Test anonymous search query"""
        query = SearchQuery.objects.create(query="smartphone", results_count=10)
        assert query.query == "smartphone"
        assert query.searcher is None


@pytest.mark.django_db
class TestPromoCode:
    """Tests for PromoCode model"""

    def test_promo_code_creation(self):
        """Test promo code creation"""
        now = timezone.now()
        promo = PromoCode.objects.create(
            code="SAVE10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )
        assert promo.code == "SAVE10"
        assert promo.discount_type == "percentage"
        assert promo.discount_value == Decimal("10.00")

    def test_promo_code_is_valid(self):
        """Test is_valid method"""
        now = timezone.now()

        # Valid promo code
        promo = PromoCode.objects.create(
            code="VALID",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            is_active=True,
        )
        assert promo.is_valid() is True

        # Expired promo code
        expired_promo = PromoCode.objects.create(
            code="EXPIRED",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now - timedelta(days=60),
            valid_until=now - timedelta(days=30),
            is_active=True,
        )
        assert expired_promo.is_valid() is False

        # Inactive promo code
        inactive_promo = PromoCode.objects.create(
            code="INACTIVE",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
            is_active=False,
        )
        assert inactive_promo.is_valid() is False

    def test_promo_code_calculate_discount_percentage(self):
        """Test calculate_discount for percentage type"""
        now = timezone.now()
        promo = PromoCode.objects.create(
            code="SAVE10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )

        # 10% of 100 = 10
        discount = promo.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("10.00")

    def test_promo_code_calculate_discount_fixed(self):
        """Test calculate_discount for fixed amount type"""
        now = timezone.now()
        promo = PromoCode.objects.create(
            code="SAVE20",
            discount_type="fixed",
            discount_value=Decimal("20.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )

        discount = promo.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("20.00")

    def test_promo_code_max_discount(self):
        """Test max_discount_amount limit"""
        now = timezone.now()
        promo = PromoCode.objects.create(
            code="SAVE50",
            discount_type="percentage",
            discount_value=Decimal("50.00"),
            max_discount_amount=Decimal("25.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )

        # 50% of 100 = 50, but max discount is 25
        discount = promo.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("25.00")

    def test_promo_code_usage_limit(self):
        """Test usage limit checking"""
        now = timezone.now()
        promo = PromoCode.objects.create(
            code="LIMITED",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            usage_limit=5,
            usage_count=0,
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )

        # Should be valid initially
        assert promo.is_valid() is True

        # Simulate usage
        promo.usage_count = 5
        promo.save()

        # Should no longer be valid
        assert promo.is_valid() is False

    def test_promo_code_min_purchase_amount(self):
        """Test minimum purchase amount"""
        now = timezone.now()
        promo = PromoCode.objects.create(
            code="MIN50",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            min_purchase_amount=Decimal("50.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )

        # Below minimum - should return 0
        discount = promo.calculate_discount(Decimal("30.00"))
        assert discount == Decimal("0.00")

        # Above minimum - should apply discount
        discount = promo.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("10.00")
