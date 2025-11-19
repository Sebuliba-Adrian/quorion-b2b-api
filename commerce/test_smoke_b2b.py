"""
End-to-end smoke tests for B2B mode
Tests the complete workflow: Cart → Lead → Quote → Order → Delivery
"""

import uuid
import pytest
from decimal import Decimal
from django.utils import timezone

from commerce.models import (
    Cart, CartItem, Lead, QuoteRequest, QuoteRequestDetail,
    PurchaseOrder, PurchaseOrderDetail, DeliveryTerm, PaymentTerm, PaymentMode
)
from products.models import Product, ProductSKU, PackagingType, PackagingUnit
from tenants.models import Tenant, TenantAddress


@pytest.fixture
def seller_tenant(db):
    """Create seller tenant"""
    return Tenant.objects.create(
        name="B2B Seller",
        type="seller",
        email="seller@b2b.com"
    )


@pytest.fixture
def buyer_tenant(db):
    """Create buyer tenant"""
    return Tenant.objects.create(
        name="B2B Buyer",
        type="buyer",
        email="buyer@b2b.com"
    )


@pytest.fixture
def warehouse(db, seller_tenant):
    """Create warehouse address"""
    return TenantAddress.objects.create(
        tenant=seller_tenant,
        address1="123 Warehouse St",
        city="Test City",
        state="Test State",
        zip_code="12345",
        country="US",
        address_type="warehouse"
    )


@pytest.fixture
def product_with_sku(db, seller_tenant):
    """Create product with SKU"""
    product = Product.objects.create(
        seller=seller_tenant,
        name="B2B Test Product",
        description="Product for B2B testing"
    )

    pkg_type = PackagingType.objects.create(name="Box")
    pkg_unit = PackagingUnit.objects.create(name="Unit")

    sku = ProductSKU.objects.create(
        product=product,
        number="SKU-B2B-001",
        name="Test SKU",
        kind="master",
        packaging_type=pkg_type,
        packaging_unit=pkg_unit,
        package_volume=1.0
    )

    return product, sku


@pytest.fixture
def delivery_term(db):
    """Create delivery term"""
    return DeliveryTerm.objects.create(
        name="Standard Delivery",
        description="5-7 business days"
    )


@pytest.fixture
def payment_term(db):
    """Create payment term"""
    return PaymentTerm.objects.create(
        name="Net 30",
        description="Payment due in 30 days"
    )


@pytest.fixture
def payment_mode(db):
    """Create payment mode"""
    return PaymentMode.objects.create(
        name="Bank Transfer",
        description="Direct bank transfer"
    )


@pytest.mark.django_db
class TestB2BWorkflowSmoke:
    """End-to-end smoke tests for B2B workflow"""

    def test_complete_b2b_workflow(
        self, buyer_tenant, seller_tenant, product_with_sku, warehouse,
        delivery_term, payment_term, payment_mode
    ):
        """
        Test complete B2B workflow from cart to delivery
        Flow: Cart → Lead → Quote → Order → Shipment
        """
        product, sku = product_with_sku

        # ========== STEP 1: Create Cart and Add Items ==========
        cart = Cart.objects.create(buyer=buyer_tenant)

        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=Decimal("10.00"),
            unit_price=Decimal("100.00")
        )

        # Verify cart state
        assert cart.total_items == 1
        assert cart.total_quantity == Decimal("10.00")
        assert cart.subtotal == Decimal("1000.00")

        # ========== STEP 2: Convert Cart to Lead ==========
        lead = Lead.objects.create(
            seller=seller_tenant,
            cart=cart,
            buyer_email="buyer@b2b.com",
            buyer_company_name="B2B Buyer Company",
            buyer_first_name="John",
            buyer_last_name="Doe",
            buyer_phone="+1234567890"
        )
        lead.create()  # FSM transition: NO_LEAD → NEW
        lead.save()

        # Verify lead created
        assert lead.seller == seller_tenant
        assert lead.cart == cart
        assert lead.status == "new"

        # ========== STEP 3: Seller Reviews and Accepts Lead ==========
        lead.convert()  # FSM transition: NEW → CONVERTED
        lead.save()

        assert lead.status == "converted"

        # ========== STEP 4: Create Quote from Lead ==========
        quote = QuoteRequest.objects.create(
            buyer=buyer_tenant,
            seller=seller_tenant,
            warehouse=warehouse,
            delivery_term=delivery_term,
            payment_term=payment_term,
            payment_mode=payment_mode,
            number=f"QR-{uuid.uuid4().hex[:8].upper()}",
            currency="USD"
        )
        quote.create_quote()  # FSM transition: NO_REQUEST → NEW
        quote.buyer_requests()  # FSM transition: NEW → REQUESTED
        quote.save()

        # Add quote items from cart
        for item in cart.items.filter(deleted_at__isnull=True):
            QuoteRequestDetail.objects.create(
                quote_request=quote,
                product=item.product,
                sku=sku,
                no_of_units=int(item.quantity),
                total_quantity=int(item.quantity),
                price_per_unit=item.unit_price,
                currency="USD"
            )

        # Verify quote created
        assert quote.items.count() == 1
        quote_item = quote.items.first()
        assert quote_item.total_quantity == 10
        assert quote_item.price_per_unit == Decimal("100.00")

        # ========== STEP 5: Seller Responds to Quote ==========
        quote.seller_responds()  # FSM transition: REQUESTED → RESPONDED
        quote.save()

        assert quote.status == "responded"

        # ========== STEP 6: Buyer Accepts Quote ==========
        quote.buyer_accepts()  # FSM transition: RESPONDED → ACCEPTED
        quote.save()

        assert quote.status == "accepted"

        # ========== STEP 7: Convert Quote to Purchase Order ==========
        order = PurchaseOrder.objects.create(
            buyer=buyer_tenant,
            seller=seller_tenant,
            warehouse=warehouse,
            delivery_term=delivery_term,
            payment_term=payment_term,
            payment_mode=payment_mode,
            quote_request=quote,
            number=f"PO-{uuid.uuid4().hex[:8].upper()}",
            currency="USD"
        )
        order.create_order()  # FSM transition: NO_ORDER → NEW
        order.save()

        # Add order items from quote
        for quote_item in quote.items.all():
            PurchaseOrderDetail.objects.create(
                order=order,
                product=quote_item.product,
                sku=quote_item.sku,
                no_of_units=quote_item.no_of_units,
                total_quantity=quote_item.total_quantity,
                price_per_unit=quote_item.price_per_unit,
                currency="USD"
            )

        # Verify order created
        assert order.items.count() == 1
        assert order.buyer == buyer_tenant
        assert order.seller == seller_tenant

        # ========== STEP 8: Accept Order ==========
        order.accept()  # FSM transition: NEW → ACCEPTED
        order.save()

        assert order.status == "accepted"

        # ========== STEP 9: Process Order ==========
        order.make_in_progress()  # FSM transition: ACCEPTED → IN_PROGRESS
        order.save()

        assert order.status == "in_progress"

        # ========== STEP 10: Ship Order ==========
        from commerce.models import ShipmentAdvice

        shipment = ShipmentAdvice.objects.create(
            order=order,
            carrier="FedEx",
            carrier_number="TRACK123456",
            estimated_time_of_arrival=timezone.now() + timezone.timedelta(days=7)
        )

        order.ship_order()  # FSM transition: IN_PROGRESS → SHIPPED
        order.save()

        # Verify shipment
        assert shipment.order == order
        assert shipment.carrier == "FedEx"
        assert order.status == "shipped"

        # ========== STEP 11: Complete Order ==========
        order.complete()  # FSM transition: SHIPPED → COMPLETED
        order.save()

        assert order.status == "completed"

        # ========== FINAL VERIFICATION ==========
        # Verify complete workflow
        assert cart.total_items == 1
        assert lead.status == "converted"
        assert quote.status == "accepted"
        assert order.status == "completed"
        assert order.items.count() == 1

        # Verify data integrity
        order_item = order.items.first()
        assert order_item.product == product
        assert order_item.total_quantity == 10
        assert order_item.price_per_unit == Decimal("100.00")

        print("✅ B2B Workflow Smoke Test PASSED")
        print(f"   Cart Items: {cart.total_items}")
        print(f"   Lead Status: {lead.status}")
        print(f"   Quote Status: {quote.status}")
        print(f"   Order Status: {order.status}")
        print(f"   Order Total: ${order.total}")


    def test_b2b_negotiation_cycle(
        self, buyer_tenant, seller_tenant, product_with_sku, warehouse,
        delivery_term, payment_term, payment_mode
    ):
        """
        Test B2B negotiation with multiple quote revisions
        """
        product, sku = product_with_sku

        # Create initial quote
        quote = QuoteRequest.objects.create(
            buyer=buyer_tenant,
            seller=seller_tenant,
            warehouse=warehouse,
            delivery_term=delivery_term,
            payment_term=payment_term,
            payment_mode=payment_mode,
            number=f"QR-{uuid.uuid4().hex[:8].upper()}",
            currency="USD"
        )
        quote.create_quote()  # FSM transition: NO_REQUEST → NEW
        quote.buyer_requests()  # FSM transition: NEW → REQUESTED
        quote.save()

        QuoteRequestDetail.objects.create(
            quote_request=quote,
            product=product,
            sku=sku,
            no_of_units=10,
            total_quantity=10,
            price_per_unit=Decimal("100.00"),
            currency="USD"
        )

        # ========== Negotiation Round 1 ==========
        # Seller responds with price
        quote.seller_responds()  # FSM transition: REQUESTED → RESPONDED
        quote.save()

        # ========== Negotiation Round 2 ==========
        # Buyer negotiates (requests lower price)
        quote.buyer_responds()  # FSM transition: RESPONDED → REQUESTED (re-negotiation)
        quote.save()

        # Update price
        quote_item = quote.items.first()
        quote_item.price_per_unit = Decimal("95.00")  # Seller reduces price
        quote_item.save()

        # ========== Negotiation Round 3 ==========
        # Seller responds with new price
        quote.seller_responds()  # FSM transition: REQUESTED → RESPONDED
        quote.save()

        # ========== Final ==========
        # Buyer accepts
        quote.buyer_accepts()  # FSM transition: RESPONDED → ACCEPTED
        quote.save()

        # Verify negotiation completed
        assert quote.status == "accepted"
        assert quote.items.first().price_per_unit == Decimal("95.00")

        print("✅ B2B Negotiation Cycle Test PASSED")
        print(f"   Final Price: ${quote.items.first().price_per_unit}")


    def test_b2b_lead_rejection(self, buyer_tenant, seller_tenant):
        """
        Test lead rejection workflow (distributor rejection)
        """
        cart = Cart.objects.create(buyer=buyer_tenant)

        lead = Lead.objects.create(
            seller=seller_tenant,
            buyer_email="buyer@test.com",
            buyer_company_name="Test Company",
            buyer_first_name="Jane",
            buyer_last_name="Smith"
        )
        lead.create()  # FSM transition: NO_LEAD → NEW
        lead.send_to_distributor()  # FSM transition: NEW → SENT_TO_DISTRIBUTOR
        lead.reject_by_distributor()  # FSM transition: SENT_TO_DISTRIBUTOR → REJECTED_BY_DISTRIBUTOR
        lead.save()

        assert lead.status == "rejected_by_distributor"

        print("✅ B2B Lead Rejection Test PASSED")


    def test_b2b_quote_rejection(
        self, buyer_tenant, seller_tenant, product_with_sku, warehouse,
        delivery_term, payment_term, payment_mode
    ):
        """
        Test quote rejection workflow
        """
        product, sku = product_with_sku

        quote = QuoteRequest.objects.create(
            buyer=buyer_tenant,
            seller=seller_tenant,
            warehouse=warehouse,
            delivery_term=delivery_term,
            payment_term=payment_term,
            payment_mode=payment_mode,
            number=f"QR-{uuid.uuid4().hex[:8].upper()}",
            currency="USD"
        )
        quote.create_quote()  # FSM transition: NO_REQUEST → NEW
        quote.buyer_requests()  # FSM transition: NEW → REQUESTED
        quote.seller_declines()  # FSM transition: REQUESTED → DECLINED
        quote.save()

        assert quote.status == "declined"

        print("✅ B2B Quote Rejection Test PASSED")


    def test_b2b_order_cancellation(
        self, buyer_tenant, seller_tenant, warehouse,
        delivery_term, payment_term, payment_mode
    ):
        """
        Test order cancellation workflow
        """
        order = PurchaseOrder.objects.create(
            buyer=buyer_tenant,
            seller=seller_tenant,
            warehouse=warehouse,
            delivery_term=delivery_term,
            payment_term=payment_term,
            payment_mode=payment_mode,
            number=f"PO-{uuid.uuid4().hex[:8].upper()}",
            currency="USD"
        )
        order.create_order()  # FSM transition: NO_ORDER → NEW
        order.accept()  # FSM transition: NEW → ACCEPTED
        order.save()

        # Cancel order
        order.cancel()  # FSM transition: ACCEPTED → CANCELLED
        order.save()

        assert order.status == "cancelled"

        print("✅ B2B Order Cancellation Test PASSED")
