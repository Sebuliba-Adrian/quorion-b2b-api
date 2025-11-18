"""
Serializers for tenant models
"""

from rest_framework import serializers

from .marketplace_config import MarketplaceConfig, SellerMarketplace
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


class MarketplaceConfigSerializer(serializers.ModelSerializer):
    mode_display = serializers.CharField(source="get_mode_display", read_only=True)

    class Meta:
        model = MarketplaceConfig
        fields = [
            "id",
            "name",
            "is_active",
            "mode",
            "mode_display",
            "enable_shopping_cart",
            "enable_guest_checkout",
            "enable_wishlist",
            "enable_lead_generation",
            "enable_quote_negotiation",
            "require_quote_approval",
            "enable_distributor_network",
            "enable_direct_purchase",
            "enable_instant_checkout",
            "skip_quote_for_direct",
            "enable_multiple_sellers",
            "enable_seller_storefronts",
            "allow_cross_seller_cart",
            "enable_dynamic_pricing",
            "enable_volume_discounts",
            "show_prices_to_guests",
            "enable_promotional_pricing",
            "enable_customer_accounts",
            "enable_customer_portal",
            "enable_saved_addresses",
            "enable_online_payment",
            "enable_credit_terms",
            "enable_partial_payments",
            "enable_product_reviews",
            "enable_seller_ratings",
            "require_verified_purchase",
            "auto_approve_quotes",
            "auto_create_customer",
            "send_notifications",
            "min_order_value",
            "max_cart_items",
            "session_timeout_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SellerMarketplaceSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.name", read_only=True)

    class Meta:
        model = SellerMarketplace
        fields = [
            "id",
            "seller",
            "seller_name",
            "storefront_name",
            "storefront_slug",
            "description",
            "is_active",
            "allow_direct_purchase",
            "require_quote_approval",
            "min_order_value",
            "auto_accept_orders",
            "allow_negotiations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
