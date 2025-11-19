"""
Views for product management
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import ProductFilter, ProductSKUFilter
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "short_description", "brand_product_name", "slug"]
    ordering_fields = ["name", "created_at", "view_count"]
    ordering = ["-created_at"]

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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductSKUFilter
    search_fields = ["number", "name", "product__name"]
    ordering_fields = ["number", "created_at"]
    ordering = ["-created_at"]

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
