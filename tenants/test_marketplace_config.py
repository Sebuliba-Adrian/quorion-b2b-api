"""
Tests for marketplace configuration - targeting 100% coverage
"""

from decimal import Decimal

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from tenants.marketplace_config import MarketplaceConfig, MarketplaceMode, SellerMarketplace
from tenants.models import Tenant


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seller_tenant():
    return Tenant.objects.create(name="Seller Corp", type="seller", email="seller@example.com")


@pytest.fixture
def marketplace_config():
    return MarketplaceConfig.objects.create(
        name="Test Marketplace",
        mode=MarketplaceMode.B2B_NEGOTIATION,
        is_active=True,
        enable_shopping_cart=True,
        enable_lead_generation=True,
        enable_quote_negotiation=True,
    )


@pytest.fixture
def seller_marketplace(seller_tenant):
    return SellerMarketplace.objects.create(
        seller=seller_tenant,
        storefront_name="Test Storefront",
        storefront_slug="test-storefront",
        description="Test storefront description",
        is_active=True,
    )


@pytest.mark.django_db
class TestMarketplaceConfigModels:
    """Test MarketplaceConfig and SellerMarketplace models"""

    def test_marketplace_config_str(self, marketplace_config):
        """Test MarketplaceConfig __str__ method"""
        expected = f"{marketplace_config.name} ({marketplace_config.get_mode_display()})"
        assert str(marketplace_config) == expected

    def test_marketplace_config_save_deactivates_others(self):
        """Test that saving an active config deactivates others"""
        config1 = MarketplaceConfig.objects.create(name="Config 1", is_active=True)
        config2 = MarketplaceConfig.objects.create(name="Config 2", is_active=True)

        config1.refresh_from_db()
        assert config1.is_active is False
        assert config2.is_active is True

    def test_marketplace_config_save_clears_cache(self, marketplace_config):
        """Test that saving a config clears the cache"""
        cache.set("active_marketplace_config", marketplace_config)
        assert cache.get("active_marketplace_config") is not None

        marketplace_config.name = "Updated Name"
        marketplace_config.save()

        assert cache.get("active_marketplace_config") is None

    def test_get_active_config(self, marketplace_config):
        """Test getting active marketplace configuration"""
        config = MarketplaceConfig.get_active_config()
        assert config is not None
        assert config.id == marketplace_config.id
        assert config.is_active is True

    def test_get_active_config_cached(self, marketplace_config):
        """Test that active config is cached"""
        cache.delete("active_marketplace_config")
        config1 = MarketplaceConfig.get_active_config()
        config2 = MarketplaceConfig.get_active_config()

        assert config1.id == config2.id

    def test_get_active_config_none_exists(self):
        """Test get_active_config when no active config exists"""
        MarketplaceConfig.objects.all().delete()
        cache.delete("active_marketplace_config")
        config = MarketplaceConfig.get_active_config()
        assert config is None

    def test_is_feature_enabled_with_config(self, marketplace_config):
        """Test checking if a feature is enabled"""
        assert MarketplaceConfig.is_feature_enabled("enable_shopping_cart") is True
        assert MarketplaceConfig.is_feature_enabled("enable_guest_checkout") is False

    def test_is_feature_enabled_no_config(self):
        """Test is_feature_enabled when no active config exists"""
        MarketplaceConfig.objects.all().delete()
        cache.delete("active_marketplace_config")
        result = MarketplaceConfig.is_feature_enabled("enable_shopping_cart")
        assert result is False

    def test_get_marketplace_mode(self, marketplace_config):
        """Test getting marketplace mode"""
        mode = MarketplaceConfig.get_marketplace_mode()
        assert mode == MarketplaceMode.B2B_NEGOTIATION

    def test_get_marketplace_mode_no_config(self):
        """Test get_marketplace_mode when no config exists"""
        MarketplaceConfig.objects.all().delete()
        cache.delete("active_marketplace_config")
        mode = MarketplaceConfig.get_marketplace_mode()
        assert mode == MarketplaceMode.B2B_NEGOTIATION

    def test_is_b2b_mode(self, marketplace_config):
        """Test checking if system is in B2B mode"""
        assert marketplace_config.is_b2b_mode() is True

    def test_is_b2b_mode_hybrid(self):
        """Test is_b2b_mode with hybrid mode"""
        config = MarketplaceConfig.objects.create(name="Hybrid Config", mode=MarketplaceMode.HYBRID, is_active=True)
        assert config.is_b2b_mode() is True

    def test_is_b2b_mode_direct_marketplace(self):
        """Test is_b2b_mode with direct marketplace mode"""
        config = MarketplaceConfig.objects.create(
            name="Direct Config", mode=MarketplaceMode.DIRECT_MARKETPLACE, is_active=True
        )
        assert config.is_b2b_mode() is False

    def test_is_marketplace_mode(self, marketplace_config):
        """Test checking if system is in marketplace mode"""
        assert marketplace_config.is_marketplace_mode() is False

    def test_is_marketplace_mode_direct(self):
        """Test is_marketplace_mode with direct marketplace mode"""
        config = MarketplaceConfig.objects.create(
            name="Direct Config", mode=MarketplaceMode.DIRECT_MARKETPLACE, is_active=True
        )
        assert config.is_marketplace_mode() is True

    def test_is_marketplace_mode_multi_vendor(self):
        """Test is_marketplace_mode with multi-vendor mode"""
        config = MarketplaceConfig.objects.create(
            name="Multi Config", mode=MarketplaceMode.MULTI_VENDOR, is_active=True
        )
        assert config.is_marketplace_mode() is True

    def test_is_marketplace_mode_hybrid(self):
        """Test is_marketplace_mode with hybrid mode"""
        config = MarketplaceConfig.objects.create(name="Hybrid Config", mode=MarketplaceMode.HYBRID, is_active=True)
        assert config.is_marketplace_mode() is True

    def test_get_workflow_type_b2b(self, marketplace_config):
        """Test get_workflow_type for B2B mode"""
        workflow = marketplace_config.get_workflow_type()
        assert workflow == "b2b_negotiation"

    def test_get_workflow_type_direct(self):
        """Test get_workflow_type for direct marketplace mode"""
        config = MarketplaceConfig.objects.create(
            name="Direct Config", mode=MarketplaceMode.DIRECT_MARKETPLACE, is_active=True
        )
        workflow = config.get_workflow_type()
        assert workflow == "direct_purchase"

    def test_get_workflow_type_multi_vendor(self):
        """Test get_workflow_type for multi-vendor mode"""
        config = MarketplaceConfig.objects.create(
            name="Multi Config", mode=MarketplaceMode.MULTI_VENDOR, is_active=True
        )
        workflow = config.get_workflow_type()
        assert workflow == "marketplace"

    def test_get_workflow_type_hybrid_with_tenant(self, seller_tenant):
        """Test get_workflow_type for hybrid mode with user tenant"""
        from unittest.mock import Mock

        config = MarketplaceConfig.objects.create(name="Hybrid Config", mode=MarketplaceMode.HYBRID, is_active=True)

        # Create mock user with tenant attribute
        mock_user = Mock()
        mock_user.tenant = seller_tenant

        workflow = config.get_workflow_type(mock_user)
        assert workflow == "b2b_negotiation"

    def test_get_workflow_type_hybrid_without_tenant(self):
        """Test get_workflow_type for hybrid mode without user tenant"""
        config = MarketplaceConfig.objects.create(name="Hybrid Config", mode=MarketplaceMode.HYBRID, is_active=True)
        workflow = config.get_workflow_type()
        assert workflow == "direct_purchase"

    def test_seller_marketplace_str(self, seller_marketplace):
        """Test SellerMarketplace __str__ method"""
        expected = f"{seller_marketplace.storefront_name} ({seller_marketplace.seller.name})"
        assert str(seller_marketplace) == expected

    def test_seller_marketplace_get_effective_setting_with_override(self, seller_marketplace):
        """Test get_effective_setting with seller override"""
        seller_marketplace.allow_direct_purchase = True
        seller_marketplace.save()
        assert seller_marketplace.get_effective_setting("allow_direct_purchase") is True

    def test_seller_marketplace_get_effective_setting_global_fallback(self, seller_marketplace, marketplace_config):
        """Test get_effective_setting falls back to global config"""
        seller_marketplace.allow_direct_purchase = None
        seller_marketplace.save()
        result = seller_marketplace.get_effective_setting("enable_shopping_cart")
        assert result is True


@pytest.mark.django_db
class TestMarketplaceConfigHelperFunctions:
    """Test marketplace configuration helper functions"""

    def test_get_marketplace_config_helper(self, marketplace_config):
        """Test get_marketplace_config helper function"""
        from tenants.marketplace_config import get_marketplace_config

        config = get_marketplace_config()
        assert config is not None
        assert config.id == marketplace_config.id

    def test_is_feature_enabled_helper(self, marketplace_config):
        """Test is_feature_enabled helper function"""
        from tenants.marketplace_config import is_feature_enabled

        assert is_feature_enabled("enable_shopping_cart") is True
        assert is_feature_enabled("enable_guest_checkout") is False

    def test_get_marketplace_mode_helper(self, marketplace_config):
        """Test get_marketplace_mode helper function"""
        from tenants.marketplace_config import get_marketplace_mode

        mode = get_marketplace_mode()
        assert mode == MarketplaceMode.B2B_NEGOTIATION

    def test_is_b2b_mode_helper(self, marketplace_config):
        """Test is_b2b_mode helper function"""
        from tenants.marketplace_config import is_b2b_mode

        assert is_b2b_mode() is True

    def test_is_b2b_mode_helper_no_config(self):
        """Test is_b2b_mode helper when no config exists"""
        from tenants.marketplace_config import is_b2b_mode

        MarketplaceConfig.objects.all().delete()
        cache.delete("active_marketplace_config")
        assert is_b2b_mode() is True

    def test_is_marketplace_mode_helper(self, marketplace_config):
        """Test is_marketplace_mode helper function"""
        from tenants.marketplace_config import is_marketplace_mode

        assert is_marketplace_mode() is False

    def test_is_marketplace_mode_helper_no_config(self):
        """Test is_marketplace_mode helper when no config exists"""
        from tenants.marketplace_config import is_marketplace_mode

        MarketplaceConfig.objects.all().delete()
        cache.delete("active_marketplace_config")
        assert is_marketplace_mode() is False


@pytest.mark.django_db
class TestMarketplaceConfigViews:
    """Test marketplace configuration API views"""

    def test_list_marketplace_configs(self, authenticated_seller_client, marketplace_config):
        """Test listing marketplace configurations"""
        response = authenticated_seller_client.get("/api/tenants/marketplace-config/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_marketplace_config(self, authenticated_seller_client, marketplace_config):
        """Test retrieving a marketplace configuration"""
        response = authenticated_seller_client.get(f"/api/tenants/marketplace-config/{marketplace_config.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == marketplace_config.name
        assert response.data["mode"] == MarketplaceMode.B2B_NEGOTIATION

    def test_create_marketplace_config(self, authenticated_seller_client):
        """Test creating a marketplace configuration"""
        data = {
            "name": "New Marketplace",
            "mode": MarketplaceMode.DIRECT_MARKETPLACE,
            "is_active": True,
            "enable_shopping_cart": True,
            "enable_direct_purchase": True,
        }
        response = authenticated_seller_client.post("/api/tenants/marketplace-config/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Marketplace"
        assert response.data["mode"] == MarketplaceMode.DIRECT_MARKETPLACE

    def test_update_marketplace_config(self, authenticated_seller_client, marketplace_config):
        """Test updating a marketplace configuration"""
        data = {
            "name": "Updated Marketplace",
            "mode": MarketplaceMode.HYBRID,
            "is_active": True,
        }
        response = authenticated_seller_client.patch(f"/api/tenants/marketplace-config/{marketplace_config.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Marketplace"
        assert response.data["mode"] == MarketplaceMode.HYBRID

    def test_delete_marketplace_config(self, authenticated_seller_client):
        """Test deleting a marketplace configuration"""
        config = MarketplaceConfig.objects.create(name="Delete Me", is_active=False)
        config_id = config.id
        response = authenticated_seller_client.delete(f"/api/tenants/marketplace-config/{config_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not MarketplaceConfig.objects.filter(id=config_id).exists()

    def test_get_active_marketplace_config(self, authenticated_seller_client, marketplace_config):
        """Test getting active marketplace configuration"""
        response = authenticated_seller_client.get("/api/tenants/marketplace-config/active/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(marketplace_config.id)

    def test_get_active_marketplace_config_none_exists(self, authenticated_seller_client):
        """Test getting active config when none exists"""
        MarketplaceConfig.objects.all().delete()
        cache.delete("active_marketplace_config")
        response = authenticated_seller_client.get("/api/tenants/marketplace-config/active/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No active marketplace configuration found" in response.data["error"]

    def test_activate_marketplace_config(self, authenticated_seller_client):
        """Test activating a marketplace configuration"""
        config = MarketplaceConfig.objects.create(name="Inactive Config", is_active=False)
        response = authenticated_seller_client.post(f"/api/tenants/marketplace-config/{config.id}/activate/")
        assert response.status_code == status.HTTP_200_OK
        config.refresh_from_db()
        assert config.is_active is True

    def test_list_seller_marketplaces(self, authenticated_seller_client, seller_marketplace):
        """Test listing seller marketplaces"""
        response = authenticated_seller_client.get("/api/tenants/seller-marketplace/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_seller_marketplace(self, authenticated_seller_client, seller_marketplace):
        """Test retrieving a seller marketplace"""
        response = authenticated_seller_client.get(f"/api/tenants/seller-marketplace/{seller_marketplace.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["storefront_name"] == seller_marketplace.storefront_name

    def test_create_seller_marketplace(self, authenticated_seller_client, seller_tenant):
        """Test creating a seller marketplace"""
        data = {
            "seller": str(seller_tenant.id),
            "storefront_name": "New Storefront",
            "storefront_slug": "new-storefront",
            "description": "New storefront description",
            "is_active": True,
        }
        response = authenticated_seller_client.post("/api/tenants/seller-marketplace/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["storefront_name"] == "New Storefront"

    def test_update_seller_marketplace(self, authenticated_seller_client, seller_marketplace):
        """Test updating a seller marketplace"""
        data = {"storefront_name": "Updated Storefront", "allow_direct_purchase": True}
        response = authenticated_seller_client.patch(f"/api/tenants/seller-marketplace/{seller_marketplace.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["storefront_name"] == "Updated Storefront"

    def test_delete_seller_marketplace(self, authenticated_seller_client, seller_tenant):
        """Test deleting a seller marketplace"""
        marketplace = SellerMarketplace.objects.create(
            seller=seller_tenant,
            storefront_name="Delete Me",
            storefront_slug="delete-me",
        )
        marketplace_id = marketplace.id
        response = authenticated_seller_client.delete(f"/api/tenants/seller-marketplace/{marketplace_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not SellerMarketplace.objects.filter(id=marketplace_id).exists()

    def test_get_effective_settings(self, authenticated_seller_client, seller_marketplace, marketplace_config):
        """Test getting effective settings for seller marketplace"""
        seller_marketplace.allow_direct_purchase = True
        seller_marketplace.min_order_value = Decimal("100.00")
        seller_marketplace.save()

        response = authenticated_seller_client.get(f"/api/tenants/seller-marketplace/{seller_marketplace.id}/effective_settings/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["allow_direct_purchase"] is True
        assert Decimal(response.data["min_order_value"]) == Decimal("100.00")
        assert response.data["auto_accept_orders"] is False
        assert response.data["allow_negotiations"] is True
