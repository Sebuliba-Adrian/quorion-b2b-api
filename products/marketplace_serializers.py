"""
Serializers for marketplace-specific product models
"""

from rest_framework import serializers

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


class ProductCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    breadcrumb = serializers.SerializerMethodField()
    level = serializers.ReadOnlyField()

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_name",
            "image",
            "icon",
            "is_active",
            "order",
            "breadcrumb",
            "level",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_breadcrumb(self, obj):
        """Get breadcrumb path"""
        return [{"id": str(cat.id), "name": cat.name, "slug": cat.slug} for cat in obj.get_breadcrumb()]


class ProductImageSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductImage
        fields = ["id", "product", "product_name", "image_url", "alt_text", "is_primary", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ["id", "name", "slug", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = ProductAttributeValue
        fields = ["id", "attribute", "attribute_name", "value", "slug", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductVariantAttributeSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute_value.attribute.name", read_only=True)
    value = serializers.CharField(source="attribute_value.value", read_only=True)

    class Meta:
        model = ProductVariantAttribute
        fields = ["id", "attribute_value", "attribute_name", "value"]
        read_only_fields = ["id"]


class ProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku_number = serializers.CharField(source="sku.number", read_only=True)
    attributes = ProductVariantAttributeSerializer(source="attribute_values", many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "sku_number",
            "name",
            "price_adjustment",
            "stock_quantity",
            "is_active",
            "attributes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductReviewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)
    order_number = serializers.CharField(source="order.number", read_only=True, allow_null=True)

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product",
            "product_name",
            "buyer",
            "buyer_name",
            "order",
            "order_number",
            "rating",
            "title",
            "review",
            "is_verified_purchase",
            "is_approved",
            "helpful_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_verified_purchase", "created_at", "updated_at"]


class SellerRatingSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)
    order_number = serializers.CharField(source="order.number", read_only=True, allow_null=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = SellerRating
        fields = [
            "id",
            "seller",
            "seller_name",
            "buyer",
            "buyer_name",
            "order",
            "order_number",
            "rating",
            "communication_rating",
            "shipping_speed_rating",
            "product_quality_rating",
            "average_rating",
            "review",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_average_rating(self, obj):
        """Calculate average of all rating components"""
        ratings = [
            obj.rating,
            obj.communication_rating or obj.rating,
            obj.shipping_speed_rating or obj.rating,
            obj.product_quality_rating or obj.rating,
        ]
        return sum(ratings) / len(ratings)


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True, allow_null=True)

    class Meta:
        model = WishlistItem
        fields = [
            "id",
            "wishlist",
            "product",
            "product_name",
            "product_slug",
            "variant",
            "variant_name",
            "notes",
            "added_at",
        ]
        read_only_fields = ["id", "added_at"]


class WishlistSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "buyer",
            "buyer_name",
            "name",
            "is_public",
            "is_active",
            "items",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_item_count(self, obj):
        """Get number of items in wishlist"""
        return obj.items.count()


class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ["id", "name", "slug", "created_at"]
        read_only_fields = ["id", "created_at"]


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku_number = serializers.CharField(source="sku.number", read_only=True)
    warehouse_name = serializers.SerializerMethodField()
    quantity_total = serializers.ReadOnlyField()
    needs_reorder = serializers.ReadOnlyField()

    class Meta:
        model = Inventory
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "sku_number",
            "variant",
            "warehouse",
            "warehouse_name",
            "quantity_available",
            "quantity_reserved",
            "quantity_incoming",
            "quantity_total",
            "reorder_level",
            "reorder_quantity",
            "needs_reorder",
            "last_restocked_at",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def get_warehouse_name(self, obj):
        """Get warehouse address as string"""
        return f"{obj.warehouse.city}, {obj.warehouse.state}"
