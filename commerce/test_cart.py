"""
Comprehensive tests for shopping cart functionality
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import Tenant, TenantType
from products.models import Product
from commerce.models import Cart, CartItem, Lead, SalesLeadStatus


@pytest.fixture
def api_client():
    """Create API client"""
    return APIClient()


@pytest.fixture
def buyer_tenant():
    """Create buyer tenant"""
    return Tenant.objects.create(
        name="Test Buyer",
        type=TenantType.BUYER,
        email="buyer@test.com"
    )


@pytest.fixture
def seller_tenant():
    """Create seller tenant"""
    return Tenant.objects.create(
        name="Test Seller",
        type=TenantType.SELLER,
        email="seller@test.com"
    )


@pytest.fixture
def product(seller_tenant):
    """Create test product"""
    return Product.objects.create(
        seller=seller_tenant,
        name="Test Product",
        description="Test product description",
        brand_product_name="Test Brand Product"
    )


@pytest.fixture
def cart(buyer_tenant):
    """Create test cart"""
    return Cart.objects.create(buyer=buyer_tenant)


@pytest.fixture
def cart_with_items(cart, product):
    """Create cart with items"""
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=Decimal('5.00'),
        unit_price=Decimal('100.00')
    )
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
        assert cart_with_items.total_quantity == Decimal('5.00')

    def test_cart_subtotal(self, cart_with_items):
        """Test subtotal calculation"""
        assert cart_with_items.subtotal == Decimal('500.00')

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
            cart=cart,
            product=product,
            quantity=Decimal('10.00'),
            unit_price=Decimal('50.00')
        )
        assert item.id is not None
        assert item.cart == cart
        assert item.product == product
        assert item.quantity == Decimal('10.00')
        assert item.unit_price == Decimal('50.00')

    def test_cart_item_total_price(self, cart, product):
        """Test total_price calculation"""
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=Decimal('3.50'),
            unit_price=Decimal('25.00')
        )
        assert item.total_price == Decimal('87.50')

    def test_cart_item_unique_constraint(self, cart, product):
        """Test unique constraint on cart and product"""
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('10.00')
        )

        with pytest.raises(Exception):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=Decimal('2.00'),
                unit_price=Decimal('20.00')
            )

    def test_cart_item_soft_delete(self, cart, product):
        """Test soft delete functionality"""
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('10.00')
        )

        assert item.deleted_at is None
        item.soft_delete()
        assert item.deleted_at is not None


@pytest.mark.django_db
class TestCartAPI:
    """Test Cart API endpoints"""

    def test_create_cart(self, api_client, buyer_tenant):
        """Test creating a cart via API"""
        response = api_client.post('/api/commerce/carts/', {
            'buyer': str(buyer_tenant.id),
            'is_active': True
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data['buyer']) == str(buyer_tenant.id)
        assert response.data['is_active'] is True

    def test_list_carts(self, api_client, cart):
        """Test listing carts"""
        response = api_client.get('/api/commerce/carts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_cart(self, api_client, cart):
        """Test retrieving a specific cart"""
        response = api_client.get(f'/api/commerce/carts/{cart.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(cart.id)

    def test_update_cart(self, api_client, cart):
        """Test updating a cart"""
        response = api_client.patch(f'/api/commerce/carts/{cart.id}/', {
            'is_active': False
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    def test_delete_cart(self, api_client, cart):
        """Test deleting a cart"""
        response = api_client.delete(f'/api/commerce/carts/{cart.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Cart.objects.filter(id=cart.id).count() == 0


@pytest.mark.django_db
class TestCartItemAPI:
    """Test CartItem API endpoints"""

    def test_add_item_to_cart(self, api_client, cart, product):
        """Test adding item to cart"""
        response = api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '5.00',
            'unit_price': '100.00',
            'notes': 'Test notes'
        })
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['quantity'] == '5.00'
        assert response.data['unit_price'] == '100.00'

    def test_update_cart_item_quantity(self, api_client, cart, product):
        """Test updating item quantity"""
        api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '2.00',
            'unit_price': '50.00'
        })

        response = api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '10.00',
            'unit_price': '50.00'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['quantity'] == '10.00'

    def test_add_item_missing_fields(self, api_client, cart):
        """Test adding item with missing required fields"""
        response = api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'quantity': '5.00'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_item_from_cart(self, api_client, cart_with_items):
        """Test removing item from cart"""
        item = cart_with_items.items.first()
        response = api_client.post(f'/api/commerce/carts/{cart_with_items.id}/remove_item/', {
            'item_id': str(item.id)
        })
        assert response.status_code == status.HTTP_200_OK

        item.refresh_from_db()
        assert item.deleted_at is not None

    def test_remove_non_existent_item(self, api_client, cart):
        """Test removing non-existent item"""
        import uuid
        response = api_client.post(f'/api/commerce/carts/{cart.id}/remove_item/', {
            'item_id': str(uuid.uuid4())
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_clear_cart(self, api_client, cart_with_items):
        """Test clearing all items from cart"""
        assert cart_with_items.total_items == 1

        response = api_client.post(f'/api/commerce/carts/{cart_with_items.id}/clear/')
        assert response.status_code == status.HTTP_200_OK

        cart_with_items.refresh_from_db()
        assert cart_with_items.total_items == 0


@pytest.mark.django_db
class TestCartToLeadConversion:
    """Test converting cart to lead"""

    def test_convert_cart_to_lead(self, api_client, cart_with_items, seller_tenant):
        """Test successful cart to lead conversion"""
        response = api_client.post(f'/api/commerce/carts/{cart_with_items.id}/convert_to_lead/', {
            'seller': str(seller_tenant.id),
            'buyer_first_name': 'John',
            'buyer_last_name': 'Doe',
            'buyer_email': 'john@example.com',
            'buyer_phone': '+1234567890',
            'buyer_company_name': 'Test Company'
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['seller'] == str(seller_tenant.id)
        assert response.data['buyer_first_name'] == 'John'
        assert response.data['buyer_email'] == 'john@example.com'
        assert response.data['status'] == SalesLeadStatus.NEW

        cart_with_items.refresh_from_db()
        assert cart_with_items.is_active is False

        lead = Lead.objects.get(id=response.data['id'])
        assert lead.cart == cart_with_items

    def test_convert_empty_cart_to_lead(self, api_client, cart, seller_tenant):
        """Test converting empty cart to lead"""
        response = api_client.post(f'/api/commerce/carts/{cart.id}/convert_to_lead/', {
            'seller': str(seller_tenant.id),
            'buyer_first_name': 'John',
            'buyer_last_name': 'Doe',
            'buyer_email': 'john@example.com'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_convert_cart_missing_required_fields(self, api_client, cart_with_items):
        """Test converting cart with missing required fields"""
        response = api_client.post(f'/api/commerce/carts/{cart_with_items.id}/convert_to_lead/', {
            'buyer_first_name': 'John'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCartFiltering:
    """Test cart filtering"""

    def test_filter_by_buyer(self, api_client, buyer_tenant):
        """Test filtering carts by buyer"""
        Cart.objects.create(buyer=buyer_tenant)

        response = api_client.get(f'/api/commerce/carts/?buyer={buyer_tenant.id}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_by_active_status(self, api_client, buyer_tenant):
        """Test filtering by active status"""
        Cart.objects.create(buyer=buyer_tenant, is_active=True)
        Cart.objects.create(buyer=buyer_tenant, is_active=False)

        response = api_client.get('/api/commerce/carts/?is_active=true')
        assert response.status_code == status.HTTP_200_OK
        # Handle both list and paginated responses
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        for cart in results:
            assert cart['is_active'] is True


@pytest.mark.django_db
class TestCartIntegration:
    """Test cart integration with other models"""

    def test_cart_with_multiple_products(self, api_client, cart, product, seller_tenant):
        """Test cart with multiple different products"""
        product2 = Product.objects.create(
            seller=seller_tenant,
            name="Product 2",
            description="Second product",
            brand_product_name="Test Brand Product 2"
        )

        api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '3.00',
            'unit_price': '100.00'
        })

        api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product2.id),
            'quantity': '2.00',
            'unit_price': '200.00'
        })

        response = api_client.get(f'/api/commerce/carts/{cart.id}/')
        assert response.data['total_items'] == 2
        assert float(response.data['subtotal']) == 700.00

    def test_cart_item_with_notes(self, api_client, cart, product):
        """Test cart item with custom notes"""
        response = api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '1.00',
            'unit_price': '50.00',
            'notes': 'Urgent delivery required'
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['notes'] == 'Urgent delivery required'


@pytest.mark.django_db
class TestCartEdgeCases:
    """Test cart edge cases"""

    def test_cart_with_zero_quantity(self, api_client, cart, product):
        """Test adding item with invalid quantity"""
        response = api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '0.00',
            'unit_price': '100.00'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cart_with_negative_price(self, api_client, cart, product):
        """Test adding item with negative price"""
        response = api_client.post(f'/api/commerce/carts/{cart.id}/add_item/', {
            'product': str(product.id),
            'quantity': '1.00',
            'unit_price': '-50.00'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deleted_items_not_in_cart_count(self, cart_with_items):
        """Test that deleted items don't count in totals"""
        initial_total = cart_with_items.total_items

        item = cart_with_items.items.first()
        item.soft_delete()

        assert cart_with_items.total_items == initial_total - 1
        assert cart_with_items.subtotal == Decimal('0.00')
