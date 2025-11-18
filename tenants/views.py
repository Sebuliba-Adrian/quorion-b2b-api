"""
Views for tenant management
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Tenant, TenantAddress, TenantAssociation
from .serializers import TenantSerializer, TenantAddressSerializer, TenantAssociationSerializer


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
