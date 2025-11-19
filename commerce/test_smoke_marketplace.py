"""
End-to-end smoke tests for Marketplace mode
Tests the complete workflow: Cart → Checkout → Payment → Order → Delivery
"""

import uuid
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from commerce.models import (
    Cart, CartItem, PurchaseOrder, PurchaseOrderDetail,
    DeliveryTerm, PaymentTerm, PaymentMode
)
from commerce.marketplace_models import (
    DirectCheckout, Payment, PromoCode, Notification, ProductView, SearchQuery
)
from products.models import Product, ProductSKU, PackagingType, PackagingUnit, ListPrice
from products.marketplace_models import (
    ProductCategory, ProductImage, ProductReview, SellerRating,
    Wishlist, WishlistItem, ProductTag, Inventory
)
from tenants.models import Tenant, TenantAddress


@pytest.fixture
def seller_tenant(db):
    """Create seller tenant"""
    return Tenant.objects.create(
        name="Marketplace Seller",
        type="seller",
        email="seller@marketplace.com"
    )


@pytest.fixture
def buyer_tenant(db):
    """Create buyer tenant"""
    return Tenant.objects.create(
        name="Marketplace Buyer",
        type="buyer",
        email="buyer@marketplace.com"
    )


@pytest.fixture
def category(db):
    """Create product category"""
    return ProductCategory.objects.create(
        name="Electronics",
        slug="electronics",
        is_active=True
    )


@pytest.fixture
def product_with_all_features(db, seller_tenant, category):
    """Create product with all marketplace features"""
    # Create product
    product = Product.objects.create(
        seller=seller_tenant,
        name="Marketplace Test Product",
        description="Full-featured marketplace product",
        category=category,
        is_active=True,
        status="published",
        is_featured=True
    )

    # Add tags
    tag1 = ProductTag.objects.create(name="Best Seller", slug="best-seller")
    tag2 = ProductTag.objects.create(name="New", slug="new")
    product.tags.add(tag1, tag2)

    # Add images
    ProductImage.objects.create(
        product=product,
        image_url="https://example.com/product1.jpg",
        alt_text="Main view",
        is_primary=True,
        order=1
    )
    ProductImage.objects.create(
        product=product,
        image_url="https://example.com/product2.jpg",
        alt_text="Side view",
        is_primary=False,
        order=2
    )

    # Create SKU
    pkg_type = PackagingType.objects.create(name="Box")
    pkg_unit = PackagingUnit.objects.create(name="Unit")

    sku = ProductSKU.objects.create(
        product=product,
        number="SKU-MKT-001",
        name="Marketplace SKU",
        kind="master",
        packaging_type=pkg_type,
        packaging_unit=pkg_unit,
        package_volume=1.0,
        is_active=True
    )

    # Add list price
    ListPrice.objects.create(
        sku=sku,
        price=Decimal("99.99"),
        currency="USD",
        is_active=True
    )

    return product, sku


@pytest.fixture
def warehouse(db, seller_tenant):
    """Create warehouse address"""
    return TenantAddress.objects.create(
        tenant=seller_tenant,
        address1="456 Marketplace Ave",
        city="Test City",
        state="Test State",
        zip_code="54321",
        country="US",
        address_type="warehouse"
    )


@pytest.fixture
def shipping_address(db, buyer_tenant):
    """Create shipping address"""
    return TenantAddress.objects.create(
        tenant=buyer_tenant,
        address1="789 Buyer St",
        city="Buyer City",
        state="Buyer State",
        zip_code="98765",
        country="US",
        address_type="shipping"
    )


@pytest.fixture
def delivery_term(db):
    """Create delivery term"""
    return DeliveryTerm.objects.create(
        name="Express Delivery",
        description="2-3 business days"
    )


@pytest.fixture
def payment_term(db):
    """Create payment term"""
    return PaymentTerm.objects.create(
        name="Immediate Payment",
        description="Pay on checkout"
    )


@pytest.fixture
def payment_mode(db):
    """Create payment mode"""
    return PaymentMode.objects.create(
        name="Credit Card",
        description="Stripe payment"
    )


@pytest.mark.django_db
class TestMarketplaceWorkflowSmoke:
    """End-to-end smoke tests for Marketplace workflow"""

    def test_complete_marketplace_workflow(
        self, buyer_tenant, seller_tenant, product_with_all_features, warehouse,
        shipping_address, delivery_term, payment_term, payment_mode
    ):
        """
        Test complete marketplace workflow from browsing to delivery
        Flow: Browse → Cart → Checkout → Payment → Order → Delivery
        """
        product, sku = product_with_all_features

        # ========== STEP 1: Customer Browses and Views Product ==========
        # Track product view
        view = ProductView.objects.create(
            product=product,
            viewer=buyer_tenant,
            ip_address="192.168.1.1"
        )

        assert view.product == product
        assert product.view_count == 0  # Would be updated in real app

        # ========== STEP 2: Customer Searches for Products ==========
        search = SearchQuery.objects.create(
            query="marketplace test",
            searcher=buyer_tenant,
            results_count=1
        )

        assert search.query == "marketplace test"

        # ========== STEP 3: Create Cart and Add Items ==========
        cart = Cart.objects.create(buyer=buyer_tenant)

        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("99.99")
        )

        # Verify cart
        assert cart.total_items == 1
        assert cart.total_quantity == Decimal("2.00")
        assert cart.subtotal == Decimal("199.98")

        # ========== STEP 4: Add to Wishlist (Optional) ==========
        wishlist = Wishlist.objects.create(
            buyer=buyer_tenant,
            name="My Wishlist",
            is_public=False
        )

        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=product,
            notes="Maybe buy later"
        )

        assert wishlist.items.count() == 1

        # ========== STEP 5: Create Direct Checkout ==========
        checkout = DirectCheckout.objects.create(
            cart=cart,
            buyer=buyer_tenant,
            shipping_address=shipping_address,
            billing_address=shipping_address,
            payment_method="credit_card",
            delivery_term=delivery_term,
            payment_term=payment_term,
            subtotal=Decimal("0.00"),  # Will be calculated
            tax_amount=Decimal("15.00"),
            shipping_cost=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            currency="USD"
        )

        # ========== STEP 6: Apply Promo Code ==========
        promo = PromoCode.objects.create(
            code="SAVE10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30),
            is_active=True
        )

        # Validate promo code
        assert promo.is_valid() is True

        # Apply discount
        discount = promo.calculate_discount(cart.subtotal)
        checkout.discount_amount = discount
        promo.usage_count += 1
        promo.save()

        assert discount == Decimal("19.998")

        # ========== STEP 7: Calculate Checkout Totals ==========
        checkout.calculate_totals()

        # subtotal (199.98) + tax (15.00) + shipping (10.00) - discount (19.998) ≈ 204.98
        expected_total = Decimal("204.98").quantize(Decimal("0.01"))
        actual_total = checkout.total_amount.quantize(Decimal("0.01"))

        assert actual_total == expected_total

        # ========== STEP 8: Create Order from Checkout ==========
        order = PurchaseOrder.objects.create(
            buyer=buyer_tenant,
            seller=seller_tenant,
            warehouse=warehouse,
            delivery_term=delivery_term,
            payment_term=payment_term,
            payment_mode=payment_mode,
            number=f"PO-{uuid.uuid4().hex[:8].upper()}",
            currency="USD",
            shipping_cost=checkout.shipping_cost
        )
        order.create_order()  # FSM transition: NO_ORDER → NEW
        order.save()

        # ========== STEP 9: Process Payment ==========
        payment = Payment.objects.create(
            order=order,
            payment_method="credit_card",
            amount=checkout.total_amount,
            currency="USD",
            status="pending"
        )

        # Simulate Stripe payment processing
        payment.status = "completed"
        payment.paid_at = timezone.now()
        payment.transaction_id = "txn_test_123456"
        payment.save()

        assert payment.status == "completed"
        assert payment.paid_at is not None

        # Add order items from cart
        for item in cart.items.filter(deleted_at__isnull=True):
            PurchaseOrderDetail.objects.create(
                order=order,
                product=item.product,
                sku=sku,
                no_of_units=int(item.quantity),
                total_quantity=int(item.quantity),
                price_per_unit=item.unit_price,
                currency="USD"
            )

        # ========== STEP 10: Complete Checkout ==========
        checkout.is_completed = True
        checkout.completed_at = timezone.now()
        checkout.order = order
        checkout.save()

        # ========== STEP 11: Clear Cart ==========
        cart.is_active = False
        cart.save()

        assert cart.is_active is False

        # ========== STEP 12: Send Notification ==========
        notification = Notification.objects.create(
            recipient=buyer_tenant,
            notification_type="order_update",
            title="Order Confirmed",
            message=f"Your order has been confirmed. Total: ${checkout.total_amount}",
            is_read=False
        )

        assert notification.is_read is False

        # ========== STEP 13: Update Inventory ==========
        inventory = Inventory.objects.create(
            product=product,
            sku=sku,
            warehouse=warehouse,
            quantity_available=100,
            quantity_reserved=0,
            quantity_incoming=0,
            reorder_level=20
        )

        # Reserve inventory for order
        inventory.quantity_available -= 2
        inventory.quantity_reserved += 2
        inventory.save()

        assert inventory.quantity_available == 98
        assert inventory.quantity_reserved == 2

        # ========== STEP 14: Ship Order ==========
        from commerce.models import ShipmentAdvice

        # Accept order first
        order.accept()  # FSM transition: NEW → ACCEPTED
        order.save()

        shipment = ShipmentAdvice.objects.create(
            order=order,
            carrier="DHL",
            carrier_number="DHL123456",
            estimated_time_of_arrival=timezone.now() + timedelta(days=3)
        )

        order.ship_order()  # FSM transition: ACCEPTED → SHIPPED
        order.save()

        # Send shipping notification
        shipping_notification = Notification.objects.create(
            recipient=buyer_tenant,
            notification_type="shipping_update",
            title="Order Shipped",
            message=f"Your order has been shipped via {shipment.carrier}",
            is_read=False
        )

        # Update inventory (release reservation)
        inventory.quantity_reserved -= 2
        inventory.save()

        assert inventory.quantity_reserved == 0

        # ========== STEP 15: Complete Order ==========
        order.complete()  # FSM transition: SHIPPED → COMPLETED
        order.save()

        # Send delivery notification
        Notification.objects.create(
            recipient=buyer_tenant,
            notification_type="order_update",
            title="Order Completed",
            message="Your order has been completed!",
            is_read=False
        )

        # ========== STEP 16: Customer Leaves Review ==========
        review = ProductReview.objects.create(
            product=product,
            buyer=buyer_tenant,
            order=order,
            rating=5,
            title="Excellent product!",
            review="Very satisfied with this purchase. Fast delivery!",
            is_verified_purchase=True,
            is_approved=False  # Pending moderation
        )

        assert review.rating == 5
        assert review.is_verified_purchase is True

        # ========== STEP 17: Customer Rates Seller ==========
        seller_rating = SellerRating.objects.create(
            seller=seller_tenant,
            buyer=buyer_tenant,
            order=order,
            rating=5,
            communication_rating=5,
            shipping_speed_rating=5,
            product_quality_rating=5,
            review="Great seller, highly recommended!",
            is_approved=False  # Pending moderation
        )

        assert seller_rating.rating == 5

        # ========== FINAL VERIFICATION ==========
        # Verify complete workflow
        assert cart.total_items == 1
        assert checkout.is_completed is True
        assert payment.status == "completed"
        assert order.status == "completed"
        assert order.items.count() == 1
        assert Notification.objects.filter(recipient=buyer_tenant).count() == 3
        assert review.product == product
        assert seller_rating.seller == seller_tenant
        assert inventory.quantity_available == 98

        print("✅ Marketplace Workflow Smoke Test PASSED")
        print(f"   Cart Items: {cart.total_items}")
        print(f"   Checkout Total: ${checkout.total_amount}")
        print(f"   Payment Status: {payment.status}")
        print(f"   Order Status: {order.status}")
        print(f"   Notifications: {Notification.objects.filter(recipient=buyer_tenant).count()}")
        print(f"   Product Review: {review.rating}/5 stars")
        print(f"   Seller Rating: {seller_rating.rating}/5 stars")


    def test_marketplace_with_product_features(
        self, buyer_tenant, seller_tenant, product_with_all_features
    ):
        """
        Test all product marketplace features
        """
        product, sku = product_with_all_features

        # Verify product has category
        assert product.category is not None
        assert product.category.name == "Electronics"

        # Verify product has tags
        assert product.tags.count() == 2
        tag_names = [tag.name for tag in product.tags.all()]
        assert "Best Seller" in tag_names
        assert "New" in tag_names

        # Verify product has images
        assert product.images.count() == 2
        primary_image = product.get_primary_image()
        assert primary_image is not None
        assert primary_image.is_primary is True

        # Verify product has SKU with price
        list_price = ListPrice.objects.filter(sku=sku, is_active=True).first()
        assert list_price is not None
        assert list_price.price == Decimal("99.99")

        print("✅ Marketplace Product Features Test PASSED")
        print(f"   Category: {product.category.name}")
        print(f"   Tags: {', '.join(tag_names)}")
        print(f"   Images: {product.images.count()}")
        print(f"   List Price: ${list_price.price}")


    def test_marketplace_promo_code_scenarios(self):
        """
        Test various promo code scenarios
        """
        now = timezone.now()

        # Test 1: Valid percentage discount
        promo1 = PromoCode.objects.create(
            code="PERCENT10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True
        )

        assert promo1.is_valid() is True
        discount = promo1.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("10.00")

        # Test 2: Valid fixed discount
        promo2 = PromoCode.objects.create(
            code="FIXED20",
            discount_type="fixed",
            discount_value=Decimal("20.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True
        )

        discount = promo2.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("20.00")

        # Test 3: Expired promo code
        promo3 = PromoCode.objects.create(
            code="EXPIRED",
            discount_type="percentage",
            discount_value=Decimal("15.00"),
            valid_from=now - timedelta(days=60),
            valid_until=now - timedelta(days=30),
            is_active=True
        )

        assert promo3.is_valid() is False

        # Test 4: Usage limit reached
        promo4 = PromoCode.objects.create(
            code="LIMITED",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            usage_limit=5,
            usage_count=5,
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True
        )

        assert promo4.is_valid() is False

        # Test 5: Minimum purchase requirement
        promo5 = PromoCode.objects.create(
            code="MIN50",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            min_purchase_amount=Decimal("50.00"),
            valid_from=now,
            valid_until=now + timedelta(days=30),
            is_active=True
        )

        # Below minimum
        discount = promo5.calculate_discount(Decimal("30.00"))
        assert discount == Decimal("0.00")

        # Above minimum
        discount = promo5.calculate_discount(Decimal("100.00"))
        assert discount == Decimal("10.00")

        print("✅ Marketplace Promo Code Scenarios Test PASSED")


    def test_marketplace_analytics(self, buyer_tenant, product_with_all_features):
        """
        Test marketplace analytics features
        """
        product, sku = product_with_all_features

        # Create multiple product views
        for i in range(5):
            ProductView.objects.create(
                product=product,
                viewer=buyer_tenant if i < 3 else None,  # Some anonymous
                ip_address=f"192.168.1.{i}"
            )

        # Create search queries
        SearchQuery.objects.create(
            query="electronics",
            searcher=buyer_tenant,
            results_count=10
        )
        SearchQuery.objects.create(
            query="marketplace",
            searcher=None,  # Anonymous
            results_count=5
        )

        # Verify analytics
        views = ProductView.objects.filter(product=product)
        assert views.count() == 5

        searches = SearchQuery.objects.all()
        assert searches.count() == 2

        print("✅ Marketplace Analytics Test PASSED")
        print(f"   Product Views: {views.count()}")
        print(f"   Search Queries: {searches.count()}")


    def test_marketplace_notifications(self, buyer_tenant):
        """
        Test notification system
        """
        # Create notifications
        notif1 = Notification.objects.create(
            recipient=buyer_tenant,
            notification_type="order_update",
            title="Order Confirmed",
            message="Your order has been confirmed",
            is_read=False
        )

        notif2 = Notification.objects.create(
            recipient=buyer_tenant,
            notification_type="promotion",
            title="Special Offer",
            message="Get 20% off today!",
            is_read=False
        )

        # Check unread count
        unread = Notification.objects.filter(recipient=buyer_tenant, is_read=False).count()
        assert unread == 2

        # Mark one as read
        notif1.mark_as_read()
        assert notif1.is_read is True

        # Check updated unread count
        unread = Notification.objects.filter(recipient=buyer_tenant, is_read=False).count()
        assert unread == 1

        print("✅ Marketplace Notifications Test PASSED")
        print(f"   Total Notifications: 2")
        print(f"   Unread Notifications: {unread}")
