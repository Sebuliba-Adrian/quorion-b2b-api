"""
Marketplace-specific models for products
Includes categories, images, variants, reviews, etc.
"""

import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ProductCategory(models.Model):
    """Product category with hierarchical structure"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    image = models.URLField(blank=True, null=True, help_text="Category image URL")
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon class or name")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_category"
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_ancestors(self):
        """Get all ancestor categories"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return reversed(ancestors)

    def get_descendants(self):
        """Get all descendant categories"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_breadcrumb(self):
        """Get breadcrumb path"""
        breadcrumb = list(self.get_ancestors())
        breadcrumb.append(self)
        return breadcrumb

    @property
    def level(self):
        """Get category level (0 for root, 1 for child, etc.)"""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level


class ProductImage(models.Model):
    """Product images"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(help_text="Image URL (can be CDN, S3, etc)")
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_image"
        ordering = ["-is_primary", "order", "created_at"]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductAttribute(models.Model):
    """Product attribute definition (e.g., Color, Size, Material)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_attribute"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """Product attribute value (e.g., Red, Blue, Large, Small)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_attribute_value"
        ordering = ["attribute", "value"]
        unique_together = [["attribute", "value"]]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    """Product variant (combination of attributes)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="variants")
    sku = models.ForeignKey("products.ProductSKU", on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255, help_text="Variant name (e.g., Red - Large)")
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Price adjustment from base price (+ or -)",
    )
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_variant"
        ordering = ["product", "name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductVariantAttribute(models.Model):
    """Link between variant and attribute values"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="attribute_values")
    attribute_value = models.ForeignKey(ProductAttributeValue, on_delete=models.PROTECT)

    class Meta:
        db_table = "product_variant_attribute"
        unique_together = [["variant", "attribute_value"]]

    def __str__(self):
        return f"{self.variant.name} - {self.attribute_value}"


class ProductReview(models.Model):
    """Product review from verified buyers"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="reviews")
    buyer = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="product_reviews")
    order = models.ForeignKey(
        "commerce.PurchaseOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Verified purchase order",
    )
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255, blank=True, null=True)
    review = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_review"
        ordering = ["-created_at"]
        unique_together = [["product", "buyer", "order"]]
        indexes = [
            models.Index(fields=["product", "is_approved"]),
            models.Index(fields=["buyer"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.buyer.name}"


class SellerRating(models.Model):
    """Seller rating from buyers"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="seller_ratings")
    buyer = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="given_seller_ratings")
    order = models.ForeignKey(
        "commerce.PurchaseOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related order",
    )
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    shipping_speed_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    product_quality_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    review = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seller_rating"
        ordering = ["-created_at"]
        unique_together = [["seller", "buyer", "order"]]
        indexes = [
            models.Index(fields=["seller", "is_approved"]),
        ]

    def __str__(self):
        return f"{self.seller.name} - {self.rating} stars by {self.buyer.name}"


class Wishlist(models.Model):
    """User wishlist"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="wishlists")
    name = models.CharField(max_length=255, default="My Wishlist")
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wishlist"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer.name} - {self.name}"


class WishlistItem(models.Model):
    """Wishlist item"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlist_item"
        ordering = ["-added_at"]
        unique_together = [["wishlist", "product", "variant"]]

    def __str__(self):
        return f"{self.wishlist.name} - {self.product.name}"


class ProductTag(models.Model):
    """Product tags for better organization and search"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_tag"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Inventory(models.Model):
    """Product inventory tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="inventory")
    sku = models.ForeignKey("products.ProductSKU", on_delete=models.CASCADE, related_name="inventory")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name="inventory"
    )
    warehouse = models.ForeignKey("tenants.TenantAddress", on_delete=models.CASCADE, related_name="inventory")
    quantity_available = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    quantity_reserved = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    quantity_incoming = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory"
        unique_together = [["product", "sku", "variant", "warehouse"]]
        indexes = [
            models.Index(fields=["product", "warehouse"]),
            models.Index(fields=["sku", "warehouse"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.warehouse} - {self.quantity_available} available"

    @property
    def quantity_total(self):
        """Total quantity including reserved and incoming"""
        return self.quantity_available + self.quantity_reserved + self.quantity_incoming

    @property
    def needs_reorder(self):
        """Check if inventory needs reordering"""
        return self.quantity_available <= self.reorder_level
