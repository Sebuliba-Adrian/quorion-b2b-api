"""
URLs for commerce app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet,
    CartViewSet,
    CartItemViewSet,
    LeadViewSet,
    QuoteRequestViewSet,
    QuoteRequestDetailViewSet,
    PurchaseOrderViewSet,
    PurchaseOrderDetailViewSet,
    PriceTierViewSet,
    ShipmentAdviceViewSet,
    DeliveryTermViewSet,
    PaymentTermViewSet,
    PaymentModeViewSet,
)

router = DefaultRouter()
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

urlpatterns = [
    path("", include(router.urls)),
]
