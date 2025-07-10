"""
URLs for products app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ProductViewSet, ProductSKUViewSet, PackagingTypeViewSet,
                   PackagingUnitViewSet, ListPriceViewSet)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'skus', ProductSKUViewSet, basename='product-sku')
router.register(r'packaging-types', PackagingTypeViewSet, basename='packaging-type')
router.register(r'packaging-units', PackagingUnitViewSet, basename='packaging-unit')
router.register(r'list-prices', ListPriceViewSet, basename='list-price')

urlpatterns = [
    path('', include(router.urls)),
]

