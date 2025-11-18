"""
URLs for tenant app
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MarketplaceConfigViewSet,
    SellerMarketplaceViewSet,
    TenantAddressViewSet,
    TenantAssociationViewSet,
    TenantViewSet,
)

router = DefaultRouter()
router.register(r"tenants", TenantViewSet, basename="tenant")
router.register(r"addresses", TenantAddressViewSet, basename="tenant-address")
router.register(r"associations", TenantAssociationViewSet, basename="tenant-association")
router.register(r"marketplace-config", MarketplaceConfigViewSet, basename="marketplace-config")
router.register(r"seller-marketplace", SellerMarketplaceViewSet, basename="seller-marketplace")

urlpatterns = [
    path("", include(router.urls)),
]
