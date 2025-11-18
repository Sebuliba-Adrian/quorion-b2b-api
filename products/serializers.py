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
    skus = ProductSKUSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "seller",
            "seller_name",
            "name",
            "description",
            "brand_product_name",
            "status",
            "is_active",
            "skus",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ListPriceSerializer(serializers.ModelSerializer):
    sku_number = serializers.CharField(source="sku.number", read_only=True)

    class Meta:
        model = ListPrice
        fields = ["id", "sku", "sku_number", "price", "currency", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
