"""
Marketplace configuration and feature flags system
Allows flexible configuration of marketplace behavior
"""

import uuid
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.db import models


class MarketplaceMode(models.TextChoices):
    """Different marketplace operation modes"""

    B2B_NEGOTIATION = "b2b_negotiation", "B2B Negotiation (Lead → Quote → Order)"
    DIRECT_MARKETPLACE = "direct_marketplace", "Direct Marketplace (Cart → Order)"
    HYBRID = "hybrid", "Hybrid (Both B2B and Direct)"
    MULTI_VENDOR = "multi_vendor", "Multi-Vendor Marketplace"


class MarketplaceConfig(models.Model):
    """
    Global marketplace configuration with feature flags
    Singleton pattern - only one active config at a time
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="Main Marketplace")
    is_active = models.BooleanField(default=True)

    # Marketplace Mode
    mode = models.CharField(
        max_length=50,
        choices=MarketplaceMode.choices,
        default=MarketplaceMode.B2B_NEGOTIATION,
        help_text="Primary marketplace operation mode",
    )

    # Feature Flags - Cart & Shopping
    enable_shopping_cart = models.BooleanField(default=True, help_text="Enable shopping cart functionality")
    enable_guest_checkout = models.BooleanField(
        default=False, help_text="Allow guests to checkout without registration"
    )
    enable_wishlist = models.BooleanField(default=False, help_text="Enable product wishlist feature")

    # Feature Flags - B2B Specific
    enable_lead_generation = models.BooleanField(default=True, help_text="Enable lead generation workflow")
    enable_quote_negotiation = models.BooleanField(default=True, help_text="Enable quote request and negotiation")
    require_quote_approval = models.BooleanField(default=True, help_text="Require seller approval for quotes")
    enable_distributor_network = models.BooleanField(
        default=True, help_text="Enable distributor forwarding and network"
    )

    # Feature Flags - Direct Purchase
    enable_direct_purchase = models.BooleanField(default=False, help_text="Allow direct purchase without negotiation")
    enable_instant_checkout = models.BooleanField(default=False, help_text="Enable one-click checkout")
    skip_quote_for_direct = models.BooleanField(default=False, help_text="Skip quote step for direct purchases")

    # Feature Flags - Multi-Vendor
    enable_multiple_sellers = models.BooleanField(default=True, help_text="Allow multiple sellers on platform")
    enable_seller_storefronts = models.BooleanField(default=False, help_text="Enable individual seller storefronts")
    allow_cross_seller_cart = models.BooleanField(
        default=False, help_text="Allow items from multiple sellers in one cart"
    )

    # Feature Flags - Pricing
    enable_dynamic_pricing = models.BooleanField(default=True, help_text="Enable dynamic pricing and price tiers")
    enable_volume_discounts = models.BooleanField(default=True, help_text="Enable volume-based discounts")
    show_prices_to_guests = models.BooleanField(default=False, help_text="Show prices to non-authenticated users")
    enable_promotional_pricing = models.BooleanField(default=False, help_text="Enable promotional/sale pricing")

    # Feature Flags - Customer Management
    enable_customer_accounts = models.BooleanField(
        default=True, help_text="Enable customer account creation from leads"
    )
    enable_customer_portal = models.BooleanField(default=False, help_text="Enable customer self-service portal")
    enable_saved_addresses = models.BooleanField(default=True, help_text="Allow customers to save multiple addresses")

    # Feature Flags - Payment
    enable_online_payment = models.BooleanField(default=False, help_text="Enable online payment processing")
    enable_credit_terms = models.BooleanField(default=True, help_text="Enable credit terms and net payment")
    enable_partial_payments = models.BooleanField(default=False, help_text="Allow partial/installment payments")

    # Feature Flags - Reviews & Ratings
    enable_product_reviews = models.BooleanField(default=False, help_text="Enable product reviews and ratings")
    enable_seller_ratings = models.BooleanField(default=False, help_text="Enable seller ratings")
    require_verified_purchase = models.BooleanField(default=True, help_text="Require verified purchase for reviews")

    # Workflow Settings
    auto_approve_quotes = models.BooleanField(
        default=False, help_text="Automatically approve quotes without seller action"
    )
    auto_create_customer = models.BooleanField(default=True, help_text="Automatically create customer from first order")
    send_notifications = models.BooleanField(default=True, help_text="Send email/SMS notifications")

    # Limits & Restrictions
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Minimum order value (0 = no minimum)"
    )
    max_cart_items = models.IntegerField(default=100, help_text="Maximum items allowed in cart")
    session_timeout_minutes = models.IntegerField(default=30, help_text="Shopping session timeout in minutes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "marketplace_config"
        verbose_name = "Marketplace Configuration"
        verbose_name_plural = "Marketplace Configurations"

    def __str__(self):
        return f"{self.name} ({self.get_mode_display()})"

    def save(self, *args, **kwargs):
        """Ensure only one active config exists"""
        if self.is_active:
            # Deactivate all other configs
            MarketplaceConfig.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
        # Clear cache when config changes
        cache.delete("active_marketplace_config")

    @classmethod
    def get_active_config(cls) -> Optional["MarketplaceConfig"]:
        """Get the active marketplace configuration (cached)"""
        config = cache.get("active_marketplace_config")
        if config is None:
            config = cls.objects.filter(is_active=True).first()
            if config:
                cache.set("active_marketplace_config", config, timeout=300)  # Cache for 5 minutes
        return config

    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        config = cls.get_active_config()
        if not config:
            # Default fallback behavior
            return getattr(settings, f"MARKETPLACE_{feature_name.upper()}", False)
        return getattr(config, feature_name, False)

    @classmethod
    def get_marketplace_mode(cls) -> str:
        """Get current marketplace mode"""
        config = cls.get_active_config()
        if not config:
            return MarketplaceMode.B2B_NEGOTIATION
        return config.mode

    def is_b2b_mode(self) -> bool:
        """Check if operating in B2B mode"""
        return self.mode in [MarketplaceMode.B2B_NEGOTIATION, MarketplaceMode.HYBRID]

    def is_marketplace_mode(self) -> bool:
        """Check if operating in direct marketplace mode"""
        return self.mode in [MarketplaceMode.DIRECT_MARKETPLACE, MarketplaceMode.MULTI_VENDOR, MarketplaceMode.HYBRID]

    def get_workflow_type(self, user=None) -> str:
        """Determine workflow type based on mode and user"""
        if self.mode == MarketplaceMode.B2B_NEGOTIATION:
            return "b2b_negotiation"
        elif self.mode == MarketplaceMode.DIRECT_MARKETPLACE:
            return "direct_purchase"
        elif self.mode == MarketplaceMode.MULTI_VENDOR:
            return "marketplace"
        elif self.mode == MarketplaceMode.HYBRID:
            # In hybrid mode, determine based on user type or settings
            if user and hasattr(user, "tenant"):
                return "b2b_negotiation"
            return "direct_purchase"
        return "b2b_negotiation"


class SellerMarketplace(models.Model):
    """
    Individual seller marketplace/storefront configuration
    Allows each seller to have their own marketplace settings
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.OneToOneField(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="marketplace", limit_choices_to={"type": "seller"}
    )

    # Storefront Settings
    storefront_name = models.CharField(max_length=255)
    storefront_slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Feature Overrides (can override global settings)
    allow_direct_purchase = models.BooleanField(
        default=None, null=True, blank=True, help_text="Override global direct purchase setting"
    )
    require_quote_approval = models.BooleanField(
        default=None, null=True, blank=True, help_text="Override global quote approval requirement"
    )
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Seller-specific minimum order value"
    )

    # Seller Preferences
    auto_accept_orders = models.BooleanField(default=False)
    allow_negotiations = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seller_marketplace"
        verbose_name = "Seller Marketplace"
        verbose_name_plural = "Seller Marketplaces"

    def __str__(self):
        return f"{self.storefront_name} ({self.seller.name})"

    def get_effective_setting(self, setting_name: str):
        """Get effective setting value (seller override or global)"""
        seller_value = getattr(self, setting_name, None)
        if seller_value is not None:
            return seller_value

        # Fall back to global config
        return MarketplaceConfig.is_feature_enabled(setting_name)


# Helper functions for easy access
def get_marketplace_config() -> Optional[MarketplaceConfig]:
    """Get active marketplace configuration"""
    return MarketplaceConfig.get_active_config()


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return MarketplaceConfig.is_feature_enabled(feature_name)


def get_marketplace_mode() -> str:
    """Get current marketplace mode"""
    return MarketplaceConfig.get_marketplace_mode()


def is_b2b_mode() -> bool:
    """Check if system is in B2B mode"""
    config = get_marketplace_config()
    return config.is_b2b_mode() if config else True


def is_marketplace_mode() -> bool:
    """Check if system is in marketplace mode"""
    config = get_marketplace_config()
    return config.is_marketplace_mode() if config else False
