"""
Comprehensive tests for shopping cart functionality
"""

from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from commerce.models import Cart, CartItem, Lead, SalesLeadStatus
from products.models import Product
from tenants.models import Tenant, TenantType


@pytest.fixture
def api_client():
    """Create API client"""
    return APIClient()


@pytest.fixture
def buyer_tenant():
    """Create buyer tenant"""
    return Tenant.objects.create(name="Test Buyer", type=TenantType.BUYER, email="buyer@test.com")


@pytest.fixture
def seller_tenant():
    """Create seller tenant"""
    return Tenant.objects.create(name="Test Seller", type=TenantType.SELLER, email="seller@test.com")


@pytest.fixture
def product(seller_tenant):
    """Create test product"""
    return Product.objects.create(
        seller=seller_tenant,
        name="Test Product",
        description="Test product description",
        brand_product_name="Test Brand Product",
    )


@pytest.fixture
def cart(buyer_tenant):
    """Create test cart"""
    return Cart.objects.create(buyer=buyer_tenant)


@pytest.fixture
def cart_with_items(cart, product):
    """Create cart with items"""
    CartItem.objects.create(cart=cart, product=product, quantity=Decimal("5.00"), unit_price=Decimal("100.00"))
    return cart


@pytest.mark.django_db
class TestCartModel:
    """Test Cart model"""

    def test_cart_creation(self, buyer_tenant):
        """Test creating a cart"""
        cart = Cart.objects.create(buyer=buyer_tenant)
        assert cart.id is not None
        assert cart.buyer == buyer_tenant
        assert cart.is_active is True
        assert cart.total_items == 0

    def test_cart_string_representation(self, cart):
        """Test cart __str__ method"""
        assert str(cart) == f"Cart {cart.id} - {cart.buyer.name}"

    def test_cart_total_items(self, cart_with_items):
        """Test total_items property"""
        assert cart_with_items.total_items == 1

    def test_cart_total_quantity(self, cart_with_items):
        """Test total_quantity property"""
        assert cart_with_items.total_quantity == Decimal("5.00")

    def test_cart_subtotal(self, cart_with_items):
        """Test subtotal calculation"""
        assert cart_with_items.subtotal == Decimal("500.00")

    def test_cart_clear(self, cart_with_items):
        """Test clearing cart"""
        assert cart_with_items.total_items == 1
        cart_with_items.clear()
        assert cart_with_items.total_items == 0

        items = cart_with_items.items.all()
        for item in items:
            assert item.deleted_at is not None


@pytest.mark.django_db
class TestCartItemModel:
    """Test CartItem model"""

    def test_cart_item_creation(self, cart, product):
        """Test creating a cart item"""
        item = CartItem.objects.create(
            cart=cart, product=product, quantity=Decimal("10.00"), unit_price=Decimal("50.00")
        )
        assert item.id is not None
        assert item.cart == cart
        assert item.product == product
        assert item.quantity == Decimal("10.00")
        assert item.unit_price == Decimal("50.00")

    def test_cart_item_total_price(self, cart, product):
        """Test total_price calculation"""
        item = CartItem.objects.create(
            cart=cart, product=product, quantity=Decimal("3.50"), unit_price=Decimal("25.00")
        )
        assert item.total_price == Decimal("87.50")

    def test_cart_item_unique_constraint(self, cart, product):
        """Test unique constraint on cart and product"""
        CartItem.objects.create(cart=cart, product=product, quantity=Decimal("1.00"), unit_price=Decimal("10.00"))

        with pytest.raises(Exception):
            CartItem.objects.create(cart=cart, product=product, quantity=Decimal("2.00"), unit_price=Decimal("20.00"))

    def test_cart_item_soft_delete(self, cart, product):
        """Test soft delete functionality"""
        item = CartItem.objects.create(
            cart=cart, product=product, quantity=Decimal("1.00"), unit_price=Decimal("10.00")
        )

        assert item.deleted_at is None
        item.soft_delete()
        assert item.deleted_at is not None


@pytest.mark.django_db
class TestCartAPI:
    """Test Cart API endpoints"""

    def test_create_cart(self, api_client, buyer_tenant):
        """Test creating a cart via API"""
        response = api_client.post("/api/commerce/carts/", {"buyer": str(buyer_tenant.id), "is_active": True})
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["buyer"]) == str(buyer_tenant.id)
        assert response.data["is_active"] is True

    def test_list_carts(self, api_client, cart):
        """Test listing carts"""
        response = api_client.get("/api/commerce/carts/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_cart(self, api_client, cart):
        """Test retrieving a specific cart"""
        response = api_client.get(f"/api/commerce/carts/{cart.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(cart.id)

    def test_update_cart(self, api_client, cart):
        """Test updating a cart"""
        response = api_client.patch(f"/api/commerce/carts/{cart.id}/", {"is_active": False})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_delete_cart(self, api_client, cart):
        """Test deleting a cart"""
        response = api_client.delete(f"/api/commerce/carts/{cart.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Cart.objects.filter(id=cart.id).count() == 0


@pytest.mark.django_db
class TestCartItemAPI:
    """Test CartItem API endpoints"""

    def test_add_item_to_cart(self, api_client, cart, product):
        """Test adding item to cart"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "5.00", "unit_price": "100.00", "notes": "Test notes"},
        )
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["quantity"] == "5.00"
        assert response.data["unit_price"] == "100.00"

    def test_update_cart_item_quantity(self, api_client, cart, product):
        """Test updating item quantity"""
        api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "2.00", "unit_price": "50.00"},
        )

        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "10.00", "unit_price": "50.00"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == "10.00"

    def test_add_item_missing_fields(self, api_client, cart):
        """Test adding item with missing required fields"""
        response = api_client.post(f"/api/commerce/carts/{cart.id}/add_item/", {"quantity": "5.00"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_item_from_cart(self, api_client, cart_with_items):
        """Test removing item from cart"""
        item = cart_with_items.items.first()
        response = api_client.post(f"/api/commerce/carts/{cart_with_items.id}/remove_item/", {"item_id": str(item.id)})
        assert response.status_code == status.HTTP_200_OK

        item.refresh_from_db()
        assert item.deleted_at is not None

    def test_remove_non_existent_item(self, api_client, cart):
        """Test removing non-existent item"""
        import uuid

        response = api_client.post(f"/api/commerce/carts/{cart.id}/remove_item/", {"item_id": str(uuid.uuid4())})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_clear_cart(self, api_client, cart_with_items):
        """Test clearing all items from cart"""
        assert cart_with_items.total_items == 1

        response = api_client.post(f"/api/commerce/carts/{cart_with_items.id}/clear/")
        assert response.status_code == status.HTTP_200_OK

        cart_with_items.refresh_from_db()
        assert cart_with_items.total_items == 0


@pytest.mark.django_db
class TestCartToLeadConversion:
    """Test converting cart to lead"""

    def test_convert_cart_to_lead(self, api_client, cart_with_items, seller_tenant):
        """Test successful cart to lead conversion"""
        response = api_client.post(
            f"/api/commerce/carts/{cart_with_items.id}/convert_to_lead/",
            {
                "seller": str(seller_tenant.id),
                "buyer_first_name": "John",
                "buyer_last_name": "Doe",
                "buyer_email": "john@example.com",
                "buyer_phone": "+1234567890",
                "buyer_company_name": "Test Company",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["seller"] == str(seller_tenant.id)
        assert response.data["buyer_first_name"] == "John"
        assert response.data["buyer_email"] == "john@example.com"
        assert response.data["status"] == SalesLeadStatus.NEW

        cart_with_items.refresh_from_db()
        assert cart_with_items.is_active is False

        lead = Lead.objects.get(id=response.data["id"])
        assert lead.cart == cart_with_items

    def test_convert_empty_cart_to_lead(self, api_client, cart, seller_tenant):
        """Test converting empty cart to lead"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/convert_to_lead/",
            {
                "seller": str(seller_tenant.id),
                "buyer_first_name": "John",
                "buyer_last_name": "Doe",
                "buyer_email": "john@example.com",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_convert_cart_missing_required_fields(self, api_client, cart_with_items):
        """Test converting cart with missing required fields"""
        response = api_client.post(
            f"/api/commerce/carts/{cart_with_items.id}/convert_to_lead/", {"buyer_first_name": "John"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCartFiltering:
    """Test cart filtering"""

    def test_filter_by_buyer(self, api_client, buyer_tenant):
        """Test filtering carts by buyer"""
        Cart.objects.create(buyer=buyer_tenant)

        response = api_client.get(f"/api/commerce/carts/?buyer={buyer_tenant.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_by_active_status(self, api_client, buyer_tenant):
        """Test filtering by active status"""
        Cart.objects.create(buyer=buyer_tenant, is_active=True)
        Cart.objects.create(buyer=buyer_tenant, is_active=False)

        response = api_client.get("/api/commerce/carts/?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        # Handle both list and paginated responses
        results = response.data if isinstance(response.data, list) else response.data.get("results", [])
        for cart in results:
            assert cart["is_active"] is True


@pytest.mark.django_db
class TestCartIntegration:
    """Test cart integration with other models"""

    def test_cart_with_multiple_products(self, api_client, cart, product, seller_tenant):
        """Test cart with multiple different products"""
        product2 = Product.objects.create(
            seller=seller_tenant,
            name="Product 2",
            description="Second product",
            brand_product_name="Test Brand Product 2",
        )

        api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "3.00", "unit_price": "100.00"},
        )

        api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product2.id), "quantity": "2.00", "unit_price": "200.00"},
        )

        response = api_client.get(f"/api/commerce/carts/{cart.id}/")
        assert response.data["total_items"] == 2
        assert float(response.data["subtotal"]) == 700.00

    def test_cart_item_with_notes(self, api_client, cart, product):
        """Test cart item with custom notes"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {
                "product": str(product.id),
                "quantity": "1.00",
                "unit_price": "50.00",
                "notes": "Urgent delivery required",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["notes"] == "Urgent delivery required"


@pytest.mark.django_db
class TestCartEdgeCases:
    """Test cart edge cases"""

    def test_cart_with_zero_quantity(self, api_client, cart, product):
        """Test adding item with invalid quantity"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "0.00", "unit_price": "100.00"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cart_with_negative_price(self, api_client, cart, product):
        """Test adding item with negative price"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "1.00", "unit_price": "-50.00"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deleted_items_not_in_cart_count(self, cart_with_items):
        """Test that deleted items don't count in totals"""
        initial_total = cart_with_items.total_items

        item = cart_with_items.items.first()
        item.soft_delete()

        assert cart_with_items.total_items == initial_total - 1
        assert cart_with_items.subtotal == Decimal("0.00")

@pytest.mark.django_db
class TestCartAdvancedOperations:
    """Test advanced cart operations"""

    def test_cart_clone(self, api_client, cart_with_items, buyer_tenant):
        """Test cloning a cart"""
        response = api_client.post(
            f"/api/commerce/carts/{cart_with_items.id}/clone/",
            {"buyer": str(buyer_tenant.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        
        cloned_cart_id = response.data["id"]
        assert cloned_cart_id != str(cart_with_items.id)
        
        cloned_cart = Cart.objects.get(id=cloned_cart_id)
        assert cloned_cart.total_items == cart_with_items.total_items
        assert cloned_cart.subtotal == cart_with_items.subtotal

    def test_cart_merge(self, api_client, cart_with_items, product, seller_tenant, buyer_tenant):
        """Test merging two carts"""
        # Create a second cart for merging
        cart2 = Cart.objects.create(buyer=buyer_tenant)

        product2 = Product.objects.create(
            seller=seller_tenant,
            name="Product 2",
            description="Second product",
            brand_product_name="Test Brand Product 2",
        )

        api_client.post(
            f"/api/commerce/carts/{cart2.id}/add_item/",
            {"product": str(product2.id), "quantity": "3.00", "unit_price": "75.00"}
        )

        initial_total = cart_with_items.total_items

        response = api_client.post(
            f"/api/commerce/carts/{cart_with_items.id}/merge/",
            {"other_cart_id": str(cart2.id)}
        )
        assert response.status_code == status.HTTP_200_OK

        cart_with_items.refresh_from_db()
        assert cart_with_items.total_items == initial_total + 1

        cart2.refresh_from_db()
        assert cart2.is_active is False

    def test_cart_validate_success(self, api_client, cart_with_items):
        """Test validating a valid cart"""
        response = api_client.get(f"/api/commerce/carts/{cart_with_items.id}/validate/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["errors"] == []

    def test_cart_is_anonymous(self, buyer_tenant):
        """Test is_anonymous property"""
        anonymous_cart = Cart.objects.create(session_key="test-session-123")
        assert anonymous_cart.is_anonymous is True
        
        buyer_cart = Cart.objects.create(buyer=buyer_tenant)
        assert buyer_cart.is_anonymous is False

    def test_cart_is_expired(self):
        """Test is_expired property"""
        from django.utils import timezone
        from datetime import timedelta
        
        expired_cart = Cart.objects.create(
            session_key="expired",
            expires_at=timezone.now() - timedelta(hours=1)
        )
        assert expired_cart.is_expired is True
        
        active_cart = Cart.objects.create(
            session_key="active",
            expires_at=timezone.now() + timedelta(hours=1)
        )
        assert active_cart.is_expired is False
        
        no_expiry_cart = Cart.objects.create(session_key="no-expiry")
        assert no_expiry_cart.is_expired is False

    def test_bulk_add_items(self, api_client, cart, product, seller_tenant):
        """Test adding multiple items at once"""
        product2 = Product.objects.create(
            seller=seller_tenant,
            name="Product 2",
            description="Second product",
            brand_product_name="Test Brand Product 2",
        )

        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_bulk_items/",
            {
                "items": [
                    {"product": str(product.id), "quantity": "2.00", "unit_price": "50.00"},
                    {"product": str(product2.id), "quantity": "3.00", "unit_price": "75.00"}
                ]
            },
            format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 2

        cart.refresh_from_db()
        assert cart.total_items == 2

    def test_bulk_add_empty_items(self, api_client, cart):
        """Test bulk add with empty items array"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_bulk_items/",
            {"items": []}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_clone_missing_buyer(self, api_client, cart_with_items):
        """Test cloning without buyer specified"""
        response = api_client.post(
            f"/api/commerce/carts/{cart_with_items.id}/clone/",
            {}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_merge_missing_cart_id(self, api_client, cart):
        """Test merge with missing cart ID"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/merge/",
            {}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_merge_nonexistent_cart(self, api_client, cart):
        """Test merge with non-existent cart"""
        import uuid
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/merge/",
            {"other_cart_id": str(uuid.uuid4())}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCustomerModel:
    """Test Customer model"""

    def test_customer_creation(self, seller_tenant):
        """Test creating a customer"""
        from commerce.models import Customer
        
        customer = Customer.objects.create(
            tenant=seller_tenant,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company_name="Test Company",
            credit_limit=Decimal("50000.00"),
            payment_terms_days=30
        )
        
        assert customer.id is not None
        assert customer.full_name == "John Doe"
        assert customer.email == "john.doe@example.com"
        assert customer.is_active is True

    def test_lead_to_customer_conversion(self, api_client, seller_tenant):
        """Test converting a lead to a customer"""
        from commerce.models import Lead, SalesLeadStatus

        lead = Lead.objects.create(
            seller=seller_tenant,
            buyer_first_name="Jane",
            buyer_last_name="Smith",
            buyer_email="jane.smith@example.com",
            buyer_phone="+9876543210",
            buyer_company_name="Smith Industries"
        )
        lead.create()
        lead.save()

        response = api_client.post(
            f"/api/commerce/leads/{lead.id}/convert_to_customer/",
            {"credit_limit": "100000.00", "payment_terms_days": 60}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Jane"
        assert response.data["email"] == "jane.smith@example.com"
        assert response.data["credit_limit"] == "100000.00"

        # Check lead-customer linkage without refresh_from_db (FSM field issue)
        updated_lead = Lead.objects.get(id=lead.id)
        assert updated_lead.customer is not None

    def test_customer_str_representation(self, seller_tenant):
        """Test customer string representation"""
        from commerce.models import Customer

        customer = Customer.objects.create(
            tenant=seller_tenant,
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )

        assert str(customer) == "John Doe - john@example.com"


@pytest.mark.django_db
class TestAnonymousCarts:
    """Test anonymous cart functionality"""

    def test_create_anonymous_cart(self, api_client):
        """Test creating an anonymous cart"""
        response = api_client.post(
            "/api/commerce/carts/",
            {"session_key": "anonymous-session-456", "name": "Guest Cart"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["session_key"] == "anonymous-session-456"
        assert response.data["is_anonymous"] is True

    def test_anonymous_cart_with_items(self, api_client, product):
        """Test adding items to anonymous cart"""
        cart_response = api_client.post(
            "/api/commerce/carts/",
            {"session_key": "anonymous-session-789"}
        )
        cart_id = cart_response.data["id"]
        
        item_response = api_client.post(
            f"/api/commerce/carts/{cart_id}/add_item/",
            {"product": str(product.id), "quantity": "2.00", "unit_price": "100.00"}
        )
        assert item_response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestCartItemValidation:
    """Test cart item validation"""

    def test_add_item_invalid_decimal(self, api_client, cart, product):
        """Test adding item with invalid decimal value"""
        response = api_client.post(
            f"/api/commerce/carts/{cart.id}/add_item/",
            {"product": str(product.id), "quantity": "invalid", "unit_price": "100.00"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cart_item_update_via_api(self, api_client, cart_with_items):
        """Test updating cart item directly"""
        item = cart_with_items.items.first()
        
        response = api_client.patch(
            f"/api/commerce/cart-items/{item.id}/",
            {"quantity": "10.00"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == "10.00"


@pytest.mark.django_db
class TestCartSerialization:
    """Test cart serialization"""

    def test_cart_with_customer(self, buyer_tenant, seller_tenant):
        """Test cart with customer field"""
        from commerce.models import Cart, Customer

        customer = Customer.objects.create(
            tenant=seller_tenant,
            first_name="Test",
            last_name="Customer",
            email="test@customer.com"
        )

        cart = Cart.objects.create(buyer=buyer_tenant, customer=customer)

        from commerce.serializers import CartSerializer

        serializer = CartSerializer(cart)

        assert str(serializer.data["customer"]) == str(customer.id)
        assert serializer.data["customer_name"] == "Test Customer"

