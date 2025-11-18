"""
Views for product management
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ListPrice, PackagingType, PackagingUnit, Product, ProductSKU
from .serializers import (
    ListPriceSerializer,
    PackagingTypeSerializer,
    PackagingUnitSerializer,
    ProductSerializer,
    ProductSKUSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ["seller", "status", "is_active"]

    @action(detail=True, methods=["post"])
    def create_sku(self, request, pk=None):
        """Create SKU for product"""
        product = self.get_object()
        serializer = ProductSKUSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductSKUViewSet(viewsets.ModelViewSet):
    queryset = ProductSKU.objects.all()
    serializer_class = ProductSKUSerializer
    filterset_fields = ["product", "distributor", "buyer", "kind", "is_active"]

    @action(detail=True, methods=["post"])
    def create_distributor_copy(self, request, pk=None):
        """Create distributor copy of SKU"""
        sku = self.get_object()
        distributor_id = request.data.get("distributor_id")
        if not distributor_id:
            return Response({"error": "distributor_id required"}, status=status.HTTP_400_BAD_REQUEST)

        from tenants.models import Tenant

        try:
            distributor = Tenant.objects.get(id=distributor_id, type="distributor")
        except Tenant.DoesNotExist:
            return Response({"error": "Distributor not found"}, status=status.HTTP_404_NOT_FOUND)

        distributor_sku = sku.create_distributor_copy(distributor)
        serializer = self.get_serializer(distributor_sku)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PackagingTypeViewSet(viewsets.ModelViewSet):
    queryset = PackagingType.objects.all()
    serializer_class = PackagingTypeSerializer


class PackagingUnitViewSet(viewsets.ModelViewSet):
    queryset = PackagingUnit.objects.all()
    serializer_class = PackagingUnitSerializer


class ListPriceViewSet(viewsets.ModelViewSet):
    queryset = ListPrice.objects.all()
    serializer_class = ListPriceSerializer
    filterset_fields = ["sku", "currency", "is_active"]
