"""
URLs for tenant app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantAddressViewSet, TenantAssociationViewSet

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'addresses', TenantAddressViewSet, basename='tenant-address')
router.register(r'associations', TenantAssociationViewSet, basename='tenant-association')

urlpatterns = [
    path('', include(router.urls)),
]

