from django.contrib import admin

from .marketplace_config import MarketplaceConfig, SellerMarketplace
from .models import Tenant, TenantAddress, TenantAssociation


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "email", "is_active", "created_at"]
    list_filter = ["type", "is_active"]
    search_fields = ["name", "email"]


@admin.register(TenantAddress)
class TenantAddressAdmin(admin.ModelAdmin):
    list_display = ["tenant", "address_type", "city", "state", "country", "is_active"]
    list_filter = ["address_type", "is_active", "country"]
    search_fields = ["tenant__name", "city", "state"]


@admin.register(TenantAssociation)
class TenantAssociationAdmin(admin.ModelAdmin):
    list_display = ["seller", "buyer", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["seller__name", "buyer__name"]


@admin.register(MarketplaceConfig)
class MarketplaceConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "mode", "is_active", "updated_at"]
    list_filter = ["mode", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = [
        (
            "Basic Settings",
            {
                "fields": ["name", "mode", "is_active"],
            },
        ),
        (
            "Cart & Shopping Features",
            {
                "fields": ["enable_shopping_cart", "enable_guest_checkout", "enable_wishlist"],
            },
        ),
        (
            "B2B Features",
            {
                "fields": [
                    "enable_lead_generation",
                    "enable_quote_negotiation",
                    "require_quote_approval",
                    "enable_distributor_network",
                ],
            },
        ),
        (
            "Direct Purchase Features",
            {
                "fields": ["enable_direct_purchase", "enable_instant_checkout", "skip_quote_for_direct"],
            },
        ),
        (
            "Multi-Vendor Features",
            {
                "fields": ["enable_multiple_sellers", "enable_seller_storefronts", "allow_cross_seller_cart"],
            },
        ),
        (
            "Pricing Features",
            {
                "fields": [
                    "enable_dynamic_pricing",
                    "enable_volume_discounts",
                    "show_prices_to_guests",
                    "enable_promotional_pricing",
                ],
            },
        ),
        (
            "Customer Management",
            {
                "fields": ["enable_customer_accounts", "enable_customer_portal", "enable_saved_addresses"],
            },
        ),
        (
            "Payment Features",
            {
                "fields": ["enable_online_payment", "enable_credit_terms", "enable_partial_payments"],
            },
        ),
        (
            "Reviews & Ratings",
            {
                "fields": ["enable_product_reviews", "enable_seller_ratings", "require_verified_purchase"],
            },
        ),
        (
            "Workflow Settings",
            {
                "fields": ["auto_approve_quotes", "auto_create_customer", "send_notifications"],
            },
        ),
        (
            "Limits & Restrictions",
            {
                "fields": ["min_order_value", "max_cart_items", "session_timeout_minutes"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]


@admin.register(SellerMarketplace)
class SellerMarketplaceAdmin(admin.ModelAdmin):
    list_display = ["storefront_name", "seller", "storefront_slug", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["storefront_name", "seller__name", "storefront_slug"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"storefront_slug": ["storefront_name"]}

    fieldsets = [
        (
            "Storefront Settings",
            {
                "fields": ["seller", "storefront_name", "storefront_slug", "description", "is_active"],
            },
        ),
        (
            "Feature Overrides",
            {
                "fields": ["allow_direct_purchase", "require_quote_approval", "min_order_value"],
                "description": "Leave blank to use global marketplace settings",
            },
        ),
        (
            "Seller Preferences",
            {
                "fields": ["auto_accept_orders", "allow_negotiations"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]
