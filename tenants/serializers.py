"""
Serializers for tenant models
"""

from rest_framework import serializers

from .models import Tenant, TenantAddress, TenantAssociation


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "type", "email", "phone", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantAddressSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = TenantAddress
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "address_type",
            "address1",
            "address2",
            "city",
            "state",
            "zip_code",
            "country",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantAssociationSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)

    class Meta:
        model = TenantAssociation
        fields = [
            "id",
            "seller",
            "seller_name",
            "buyer",
            "buyer_name",
            "storefront_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
