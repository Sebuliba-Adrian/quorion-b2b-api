"""
Views for tenant management
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .marketplace_config import MarketplaceConfig, SellerMarketplace
from .models import Tenant, TenantAddress, TenantAssociation
from .serializers import (
    MarketplaceConfigSerializer,
    SellerMarketplaceSerializer,
    TenantAddressSerializer,
    TenantAssociationSerializer,
    TenantSerializer,
)


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    @action(detail=True, methods=["get"])
    def addresses(self, request, pk=None):
        """Get addresses for a tenant"""
        tenant = self.get_object()
        addresses = tenant.addresses.all()
        serializer = TenantAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def distributors(self, request, pk=None):
        """Get distributors for a seller tenant"""
        tenant = self.get_object()
        if tenant.type != "seller":
            return Response({"error": "Only sellers have distributors"}, status=status.HTTP_400_BAD_REQUEST)

        associations = TenantAssociation.objects.filter(seller=tenant, is_active=True)
        distributors = [assoc.buyer for assoc in associations if assoc.buyer.type == "distributor"]
        serializer = TenantSerializer(distributors, many=True)
        return Response(serializer.data)


class TenantAddressViewSet(viewsets.ModelViewSet):
    queryset = TenantAddress.objects.all()
    serializer_class = TenantAddressSerializer
    filterset_fields = ["tenant", "address_type", "is_active"]


class TenantAssociationViewSet(viewsets.ModelViewSet):
    queryset = TenantAssociation.objects.all()
    serializer_class = TenantAssociationSerializer
    filterset_fields = ["seller", "buyer", "is_active"]


class MarketplaceConfigViewSet(viewsets.ModelViewSet):
    queryset = MarketplaceConfig.objects.all()
    serializer_class = MarketplaceConfigSerializer
    filterset_fields = ["mode", "is_active"]

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get the active marketplace configuration"""
        config = MarketplaceConfig.get_active_config()
        if not config:
            return Response({"error": "No active marketplace configuration found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate this marketplace configuration"""
        config = self.get_object()
        config.is_active = True
        config.save()
        serializer = self.get_serializer(config)
        return Response(serializer.data)


class SellerMarketplaceViewSet(viewsets.ModelViewSet):
    queryset = SellerMarketplace.objects.all()
    serializer_class = SellerMarketplaceSerializer
    filterset_fields = ["seller", "is_active"]

    @action(detail=True, methods=["get"])
    def effective_settings(self, request, pk=None):
        """Get effective settings for a seller marketplace (with global fallbacks)"""
        seller_marketplace = self.get_object()
        global_config = MarketplaceConfig.get_active_config()

        effective = {
            "allow_direct_purchase": seller_marketplace.get_effective_setting("allow_direct_purchase"),
            "require_quote_approval": seller_marketplace.get_effective_setting("require_quote_approval"),
            "min_order_value": (
                seller_marketplace.min_order_value
                if seller_marketplace.min_order_value is not None
                else (global_config.min_order_value if global_config else 0)
            ),
            "auto_accept_orders": seller_marketplace.auto_accept_orders,
            "allow_negotiations": seller_marketplace.allow_negotiations,
        }
        return Response(effective)
