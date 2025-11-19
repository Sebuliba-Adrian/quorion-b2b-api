"""
Product and SKU models
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class SKUKind(models.TextChoices):
    PRODUCT_SKU = "product_sku", "Product SKU"
    DISTRIBUTOR_SKU = "distributor_sku", "Distributor SKU"
    BUYER_SKU = "buyer_sku", "Buyer SKU"


class Product(models.Model):
    """Base product model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(
        "products.ProductCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    brand_product_name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=500, blank=True, null=True, help_text="Brief product summary")
    specifications = models.JSONField(default=dict, blank=True, help_text="Product specifications in JSON format")
    tags = models.ManyToManyField("products.ProductTag", blank=True, related_name="products")
    status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.DRAFT)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Feature this product on homepage")
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["seller", "is_active"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_featured", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.seller.name})"

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            from django.utils.text import slugify

            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_average_rating(self):
        """Get average product rating"""
        from products.marketplace_models import ProductReview

        reviews = ProductReview.objects.filter(product=self, is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg("rating"))["rating__avg"]
        return None

    def get_review_count(self):
        """Get total number of approved reviews"""
        from products.marketplace_models import ProductReview

        return ProductReview.objects.filter(product=self, is_approved=True).count()

    def get_primary_image(self):
        """Get primary product image"""
        from products.marketplace_models import ProductImage

        return ProductImage.objects.filter(product=self, is_primary=True).first()

    def increment_view_count(self):
        """Increment product view count"""
        self.view_count += 1
        self.save(update_fields=["view_count"])


class PackagingType(models.Model):
    """Packaging type (e.g., Drum, Bag, Bottle)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "packaging_type"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PackagingUnit(models.Model):
    """Packaging unit (e.g., kg, L, gal)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "packaging_unit"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductSKU(models.Model):
    """Product SKU with packaging information"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="skus")
    distributor = models.ForeignKey(
        "tenants.Tenant", on_delete=models.SET_NULL, blank=True, null=True, related_name="distributed_skus"
    )
    buyer = models.ForeignKey(
        "tenants.Tenant", on_delete=models.SET_NULL, blank=True, null=True, related_name="buyer_skus"
    )
    number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    kind = models.CharField(max_length=20, choices=SKUKind.choices, default=SKUKind.PRODUCT_SKU)
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.PROTECT)
    packaging_unit = models.ForeignKey(PackagingUnit, on_delete=models.PROTECT)
    package_volume = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_sku"
        ordering = ["product", "number"]

    def __str__(self):
        return f"{self.product.name} - {self.number}"

    def create_distributor_copy(self, distributor):
        """Create a distributor-specific copy of this SKU"""
        distributor_sku = ProductSKU.objects.create(
            product=self.product,
            distributor=distributor,
            number=self.number,
            name=self.name,
            kind=SKUKind.DISTRIBUTOR_SKU,
            packaging_type=self.packaging_type,
            packaging_unit=self.packaging_unit,
            package_volume=self.package_volume,
        )
        return distributor_sku

    def is_owned_or_distributed_by(self, tenant):
        """Check if SKU is owned or distributed by tenant"""
        if tenant == self.product.seller:
            return True
        if self.distributor and tenant == self.distributor:
            return True
        return False

    def get_total_quantity_for_units(self, no_of_units):
        """Calculate total quantity from number of units"""
        if self.package_volume:
            return no_of_units * self.package_volume
        return None


class ListPrice(models.Model):
    """Base list price for SKU"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name="list_prices")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "list_price"
        ordering = ["sku", "-created_at"]

    def __str__(self):
        return f"{self.sku.number} - {self.price} {self.currency}"


# Import marketplace models to register them with Django
from products.marketplace_models import (  # noqa: E402, F401
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
