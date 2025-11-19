"""
Serializers for product models
"""

from rest_framework import serializers

from tenants.serializers import TenantSerializer

from .models import ListPrice, PackagingType, PackagingUnit, Product, ProductSKU


class PackagingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class PackagingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingUnit
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductSKUSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    packaging_type_name = serializers.CharField(source="packaging_type.name", read_only=True)
    packaging_unit_name = serializers.CharField(source="packaging_unit.name", read_only=True)
    distributor_name = serializers.CharField(source="distributor.name", read_only=True, allow_null=True)

    class Meta:
        model = ProductSKU
        fields = [
            "id",
            "product",
            "product_name",
            "distributor",
            "distributor_name",
            "buyer",
            "number",
            "name",
            "kind",
            "packaging_type",
            "packaging_type_name",
            "packaging_unit",
            "packaging_unit_name",
            "package_volume",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, allow_null=True)
    skus = ProductSKUSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "seller",
            "seller_name",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "short_description",
            "brand_product_name",
            "specifications",
            "status",
            "is_active",
            "is_featured",
            "view_count",
            "skus",
            "primary_image",
            "average_rating",
            "review_count",
            "tag_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "view_count", "created_at", "updated_at"]

    def get_primary_image(self, obj):
        """Get primary product image URL"""
        image = obj.get_primary_image()
        return image.image_url if image else None

    def get_average_rating(self, obj):
        """Get average product rating"""
        return obj.get_average_rating()

    def get_review_count(self, obj):
        """Get total number of reviews"""
        return obj.get_review_count()

    def get_tag_names(self, obj):
        """Get list of tag names"""
        return [tag.name for tag in obj.tags.all()]


class ProductDetailSerializer(ProductSerializer):
    """Detailed product serializer with all related data"""

    from products.marketplace_serializers import ProductImageSerializer, ProductReviewSerializer

    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["images", "reviews"]


class ListPriceSerializer(serializers.ModelSerializer):
    sku_number = serializers.CharField(source="sku.number", read_only=True)

    class Meta:
        model = ListPrice
        fields = ["id", "sku", "sku_number", "price", "currency", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
