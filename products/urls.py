"""
URLs for products app
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .marketplace_views import (
    InventoryViewSet,
    ProductAttributeValueViewSet,
    ProductAttributeViewSet,
    ProductCategoryViewSet,
    ProductImageViewSet,
    ProductReviewViewSet,
    ProductTagViewSet,
    ProductVariantViewSet,
    SellerRatingViewSet,
    WishlistItemViewSet,
    WishlistViewSet,
)
from .views import ListPriceViewSet, PackagingTypeViewSet, PackagingUnitViewSet, ProductSKUViewSet, ProductViewSet

router = DefaultRouter()
# Core products
router.register(r"products", ProductViewSet, basename="product")
router.register(r"skus", ProductSKUViewSet, basename="product-sku")
router.register(r"packaging-types", PackagingTypeViewSet, basename="packaging-type")
router.register(r"packaging-units", PackagingUnitViewSet, basename="packaging-unit")
router.register(r"list-prices", ListPriceViewSet, basename="list-price")

# Marketplace features
router.register(r"categories", ProductCategoryViewSet, basename="category")
router.register(r"images", ProductImageViewSet, basename="product-image")
router.register(r"attributes", ProductAttributeViewSet, basename="attribute")
router.register(r"attribute-values", ProductAttributeValueViewSet, basename="attribute-value")
router.register(r"variants", ProductVariantViewSet, basename="variant")
router.register(r"reviews", ProductReviewViewSet, basename="review")
router.register(r"seller-ratings", SellerRatingViewSet, basename="seller-rating")
router.register(r"wishlists", WishlistViewSet, basename="wishlist")
router.register(r"wishlist-items", WishlistItemViewSet, basename="wishlist-item")
router.register(r"tags", ProductTagViewSet, basename="tag")
router.register(r"inventory", InventoryViewSet, basename="inventory")

urlpatterns = [
    path("", include(router.urls)),
]
