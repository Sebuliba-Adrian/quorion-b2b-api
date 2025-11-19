"""
Tests for marketplace product models
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from commerce.models import PurchaseOrder
from products.marketplace_models import (
    Inventory,
    ProductAttribute,
    ProductAttributeValue,
    ProductCategory,
    ProductImage,
    ProductReview,
    ProductTag,
    ProductVariant,
    ProductVariantAttribute,
    SellerRating,
    Wishlist,
    WishlistItem,
)
from products.models import Product, ProductSKU
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
def category(db):
    """Create a product category"""
    return ProductCategory.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def child_category(db, category):
    """Create a child category"""
    return ProductCategory.objects.create(name="Smartphones", slug="smartphones", parent=category)


@pytest.fixture
def product(db, seller_tenant, category):
    """Create a product"""
    return Product.objects.create(
        seller=seller_tenant, name="Test Product", description="Test description", category=category
    )


@pytest.fixture
def product_sku(db, product, seller_tenant):
    """Create a product SKU"""
    from products.models import PackagingType, PackagingUnit

    pkg_type = PackagingType.objects.create(name="Box")
    pkg_unit = PackagingUnit.objects.create(name="Piece")

    return ProductSKU.objects.create(
        product=product,
        number="SKU-001",
        name="Test SKU",
        kind="master",
        packaging_type=pkg_type,
        packaging_unit=pkg_unit,
        package_volume=1.0,
    )


@pytest.fixture
def warehouse(db, seller_tenant):
    """Create a warehouse address"""
    return TenantAddress.objects.create(
        tenant=seller_tenant,
        address1="123 Main St",
        city="Test City",
        state="Test State",
        zip_code="12345",
        country="US",
        address_type="warehouse",
    )


@pytest.mark.django_db
class TestProductCategory:
    """Tests for ProductCategory model"""

    def test_category_creation(self, category):
        """Test category creation"""
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.is_active is True
        assert category.level == 0

    def test_category_string_representation(self, category):
        """Test category __str__ method"""
        assert str(category) == "Electronics"

    def test_child_category_string_representation(self, child_category):
        """Test child category __str__ method"""
        assert str(child_category) == "Electronics > Smartphones"

    def test_category_level(self, category, child_category):
        """Test category level calculation"""
        assert category.level == 0
        assert child_category.level == 1

    def test_category_ancestors(self, child_category):
        """Test get_ancestors method"""
        ancestors = list(child_category.get_ancestors())
        assert len(ancestors) == 1
        assert ancestors[0].name == "Electronics"

    def test_category_descendants(self, category, child_category):
        """Test get_descendants method"""
        descendants = category.get_descendants()
        assert len(descendants) == 1
        assert descendants[0].name == "Smartphones"

    def test_category_breadcrumb(self, child_category):
        """Test get_breadcrumb method"""
        breadcrumb = child_category.get_breadcrumb()
        assert len(breadcrumb) == 2
        assert breadcrumb[0].name == "Electronics"
        assert breadcrumb[1].name == "Smartphones"


@pytest.mark.django_db
class TestProductImage:
    """Tests for ProductImage model"""

    def test_image_creation(self, product):
        """Test image creation"""
        image = ProductImage.objects.create(
            product=product, image_url="https://example.com/image.jpg", alt_text="Test image"
        )
        assert image.product == product
        assert image.image_url == "https://example.com/image.jpg"
        assert image.alt_text == "Test image"
        assert image.is_primary is False

    def test_primary_image_auto_unset(self, product):
        """Test that setting a new primary image unsets the old one"""
        image1 = ProductImage.objects.create(
            product=product, image_url="https://example.com/image1.jpg", is_primary=True
        )

        image2 = ProductImage.objects.create(
            product=product, image_url="https://example.com/image2.jpg", is_primary=True
        )

        image1.refresh_from_db()
        assert image1.is_primary is False
        assert image2.is_primary is True


@pytest.mark.django_db
class TestProductAttribute:
    """Tests for ProductAttribute model"""

    def test_attribute_creation(self):
        """Test attribute creation"""
        attr = ProductAttribute.objects.create(name="Color", slug="color")
        assert attr.name == "Color"
        assert attr.slug == "color"

    def test_attribute_unique_name(self):
        """Test that attribute names must be unique"""
        ProductAttribute.objects.create(name="Size", slug="size")

        with pytest.raises(IntegrityError):
            ProductAttribute.objects.create(name="Size", slug="size-2")


@pytest.mark.django_db
class TestProductAttributeValue:
    """Tests for ProductAttributeValue model"""

    def test_value_creation(self):
        """Test attribute value creation"""
        attr = ProductAttribute.objects.create(name="Color", slug="color")
        value = ProductAttributeValue.objects.create(attribute=attr, value="Red", slug="red")
        assert value.attribute == attr
        assert value.value == "Red"
        assert str(value) == "Color: Red"


@pytest.mark.django_db
class TestProductVariant:
    """Tests for ProductVariant model"""

    def test_variant_creation(self, product, product_sku):
        """Test variant creation"""
        variant = ProductVariant.objects.create(
            product=product, sku=product_sku, name="Red - Large", price_adjustment=Decimal("5.00"), stock_quantity=100
        )
        assert variant.product == product
        assert variant.name == "Red - Large"
        assert variant.price_adjustment == Decimal("5.00")
        assert variant.stock_quantity == 100


@pytest.mark.django_db
class TestProductReview:
    """Tests for ProductReview model"""

    def test_review_creation(self, product, buyer_tenant):
        """Test review creation"""
        review = ProductReview.objects.create(
            product=product,
            buyer=buyer_tenant,
            rating=5,
            title="Great product!",
            review="This product exceeded my expectations.",
        )
        assert review.product == product
        assert review.buyer == buyer_tenant
        assert review.rating == 5
        assert review.is_approved is False
        assert review.is_verified_purchase is False

    def test_review_rating_validation(self, product, buyer_tenant):
        """Test review rating must be between 1 and 5"""
        # Rating too low
        with pytest.raises(ValidationError):
            review = ProductReview(product=product, buyer=buyer_tenant, rating=0, review="Test")
            review.full_clean()

        # Rating too high
        with pytest.raises(ValidationError):
            review = ProductReview(product=product, buyer=buyer_tenant, rating=6, review="Test")
            review.full_clean()


@pytest.mark.django_db
class TestSellerRating:
    """Tests for SellerRating model"""

    def test_seller_rating_creation(self, seller_tenant, buyer_tenant):
        """Test seller rating creation"""
        rating = SellerRating.objects.create(
            seller=seller_tenant,
            buyer=buyer_tenant,
            rating=4,
            communication_rating=5,
            shipping_speed_rating=4,
            product_quality_rating=4,
            review="Good seller",
        )
        assert rating.seller == seller_tenant
        assert rating.buyer == buyer_tenant
        assert rating.rating == 4
        assert rating.is_approved is False


@pytest.mark.django_db
class TestWishlist:
    """Tests for Wishlist model"""

    def test_wishlist_creation(self, buyer_tenant):
        """Test wishlist creation"""
        wishlist = Wishlist.objects.create(buyer=buyer_tenant, name="My Wishlist")
        assert wishlist.buyer == buyer_tenant
        assert wishlist.name == "My Wishlist"
        assert wishlist.is_active is True
        assert wishlist.is_public is False

    def test_wishlist_add_item(self, buyer_tenant, product):
        """Test adding item to wishlist"""
        wishlist = Wishlist.objects.create(buyer=buyer_tenant, name="Test")

        item = WishlistItem.objects.create(wishlist=wishlist, product=product, notes="Want this for birthday")

        assert item.wishlist == wishlist
        assert item.product == product
        assert wishlist.items.count() == 1


@pytest.mark.django_db
class TestProductTag:
    """Tests for ProductTag model"""

    def test_tag_creation(self):
        """Test tag creation"""
        tag = ProductTag.objects.create(name="Featured", slug="featured")
        assert tag.name == "Featured"
        assert tag.slug == "featured"

    def test_tag_unique_slug(self):
        """Test that tag slugs must be unique"""
        ProductTag.objects.create(name="Sale", slug="sale")

        with pytest.raises(IntegrityError):
            ProductTag.objects.create(name="On Sale", slug="sale")


@pytest.mark.django_db
class TestInventory:
    """Tests for Inventory model"""

    def test_inventory_creation(self, product, product_sku, warehouse):
        """Test inventory creation"""
        inventory = Inventory.objects.create(
            product=product,
            sku=product_sku,
            warehouse=warehouse,
            quantity_available=100,
            quantity_reserved=10,
            quantity_incoming=50,
            reorder_level=20,
        )
        assert inventory.quantity_available == 100
        assert inventory.quantity_reserved == 10
        assert inventory.quantity_incoming == 50
        assert inventory.reorder_level == 20

    def test_inventory_needs_reorder(self, product, product_sku, warehouse):
        """Test needs_reorder property"""
        # Not needing reorder
        inventory = Inventory.objects.create(
            product=product, sku=product_sku, warehouse=warehouse, quantity_available=100, reorder_level=20
        )
        assert inventory.needs_reorder is False

        # Needing reorder
        inventory.quantity_available = 15
        inventory.save()
        assert inventory.needs_reorder is True
