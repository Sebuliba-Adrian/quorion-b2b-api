"""
URLs for commerce app
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .marketplace_views import (
    DirectCheckoutViewSet,
    NotificationViewSet,
    PaymentViewSet,
    ProductViewViewSet,
    PromoCodeViewSet,
    SearchQueryViewSet,
)
from .views import (
    CartItemViewSet,
    CartViewSet,
    CustomerViewSet,
    DeliveryTermViewSet,
    LeadViewSet,
    PaymentModeViewSet,
    PaymentTermViewSet,
    PriceTierViewSet,
    PurchaseOrderDetailViewSet,
    PurchaseOrderViewSet,
    QuoteRequestDetailViewSet,
    QuoteRequestViewSet,
    ShipmentAdviceViewSet,
)

router = DefaultRouter()
# Core commerce (B2B workflow)
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"carts", CartViewSet, basename="cart")
router.register(r"cart-items", CartItemViewSet, basename="cart-item")
router.register(r"leads", LeadViewSet, basename="lead")
router.register(r"quotes", QuoteRequestViewSet, basename="quote-request")
router.register(r"quote-items", QuoteRequestDetailViewSet, basename="quote-request-detail")
router.register(r"orders", PurchaseOrderViewSet, basename="purchase-order")
router.register(r"order-items", PurchaseOrderDetailViewSet, basename="purchase-order-detail")
router.register(r"price-tiers", PriceTierViewSet, basename="price-tier")
router.register(r"shipments", ShipmentAdviceViewSet, basename="shipment-advice")
router.register(r"delivery-terms", DeliveryTermViewSet, basename="delivery-term")
router.register(r"payment-terms", PaymentTermViewSet, basename="payment-term")
router.register(r"payment-modes", PaymentModeViewSet, basename="payment-mode")

# Marketplace features (Direct checkout workflow)
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"checkout", DirectCheckoutViewSet, basename="checkout")
router.register(r"product-views", ProductViewViewSet, basename="product-view")
router.register(r"search-queries", SearchQueryViewSet, basename="search-query")
router.register(r"promo-codes", PromoCodeViewSet, basename="promo-code")

urlpatterns = [
    path("", include(router.urls)),
]
