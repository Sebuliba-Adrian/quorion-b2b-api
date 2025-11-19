"""
ViewSets for marketplace-specific product features
"""

from django.db.models import Avg, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from products.marketplace_models import (
    Inventory,
    ProductAttribute,
    ProductAttributeValue,
    ProductCategory,
    ProductImage,
    ProductReview,
    ProductTag,
    ProductVariant,
    ProductVariantAttribute,
    SellerRating,
    Wishlist,
    WishlistItem,
)
from products.marketplace_serializers import (
    InventorySerializer,
    ProductAttributeSerializer,
    ProductAttributeValueSerializer,
    ProductCategorySerializer,
    ProductImageSerializer,
    ProductReviewSerializer,
    ProductTagSerializer,
    ProductVariantSerializer,
    SellerRatingSerializer,
    WishlistItemSerializer,
    WishlistSerializer,
)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["parent", "is_active"]
    search_fields = ["name", "description", "slug"]
    ordering_fields = ["name", "order", "created_at"]
    ordering = ["order", "name"]
    lookup_field = "slug"

    @action(detail=False, methods=["get"])
    def root_categories(self, request):
        """Get root categories (no parent)"""
        categories = ProductCategory.objects.filter(parent=None, is_active=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def children(self, request, slug=None):
        """Get child categories"""
        category = self.get_object()
        children = category.children.filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def products(self, request, slug=None):
        """Get products in this category"""
        from products.models import Product
        from products.serializers import ProductSerializer

        category = self.get_object()
        products = Product.objects.filter(category=category, is_active=True, status="published")
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    filterset_fields = ["product", "is_primary"]

    @action(detail=True, methods=["post"])
    def set_primary(self, request, pk=None):
        """Set this image as primary"""
        image = self.get_object()
        # Unset other primary images for this product
        ProductImage.objects.filter(product=image.product, is_primary=True).update(is_primary=False)
        image.is_primary = True
        image.save()
        serializer = self.get_serializer(image)
        return Response(serializer.data)


class ProductAttributeViewSet(viewsets.ModelViewSet):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    search_fields = ["name"]
    lookup_field = "slug"


class ProductAttributeValueViewSet(viewsets.ModelViewSet):
    queryset = ProductAttributeValue.objects.all()
    serializer_class = ProductAttributeValueSerializer
    filterset_fields = ["attribute"]


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    filterset_fields = ["product", "sku", "is_active"]


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["product", "buyer", "rating", "is_verified_purchase", "is_approved"]
    search_fields = ["title", "review", "buyer__name"]
    ordering_fields = ["rating", "created_at", "helpful_count"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a review"""
        review = self.get_object()
        review.is_approved = True
        review.save()
        serializer = self.get_serializer(review)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_helpful(self, request, pk=None):
        """Mark review as helpful"""
        review = self.get_object()
        review.helpful_count += 1
        review.save()
        serializer = self.get_serializer(review)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_product(self, request):
        """Get approved reviews for a product"""
        product_id = request.query_params.get("product_id")
        if not product_id:
            return Response({"error": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)

        reviews = ProductReview.objects.filter(product_id=product_id, is_approved=True).order_by("-created_at")
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class SellerRatingViewSet(viewsets.ModelViewSet):
    queryset = SellerRating.objects.all()
    serializer_class = SellerRatingSerializer
    filterset_fields = ["seller", "buyer", "rating", "is_approved"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a seller rating"""
        rating = self.get_object()
        rating.is_approved = True
        rating.save()
        serializer = self.get_serializer(rating)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_seller(self, request):
        """Get seller rating statistics"""
        seller_id = request.query_params.get("seller_id")
        if not seller_id:
            return Response({"error": "seller_id required"}, status=status.HTTP_400_BAD_REQUEST)

        ratings = SellerRating.objects.filter(seller_id=seller_id, is_approved=True)
        stats = ratings.aggregate(
            average_rating=Avg("rating"),
            communication_avg=Avg("communication_rating"),
            shipping_avg=Avg("shipping_speed_rating"),
            quality_avg=Avg("product_quality_rating"),
            total_ratings=Count("id"),
        )
        return Response(stats)


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["buyer", "is_public", "is_active"]
    search_fields = ["name", "description", "buyer__name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        """Add item to wishlist"""
        wishlist = self.get_object()
        product_id = request.data.get("product_id")
        variant_id = request.data.get("variant_id")
        notes = request.data.get("notes", "")

        if not product_id:
            return Response({"error": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if item already exists
        existing = WishlistItem.objects.filter(wishlist=wishlist, product_id=product_id, variant_id=variant_id).first()

        if existing:
            return Response({"error": "Item already in wishlist"}, status=status.HTTP_400_BAD_REQUEST)

        item = WishlistItem.objects.create(wishlist=wishlist, product_id=product_id, variant_id=variant_id, notes=notes)
        serializer = WishlistItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def remove_item(self, request, pk=None):
        """Remove item from wishlist"""
        wishlist = self.get_object()
        item_id = request.data.get("item_id")

        if not item_id:
            return Response({"error": "item_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = WishlistItem.objects.get(id=item_id, wishlist=wishlist)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WishlistItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        """Clear all items from wishlist"""
        wishlist = self.get_object()
        wishlist.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistItemViewSet(viewsets.ModelViewSet):
    queryset = WishlistItem.objects.all()
    serializer_class = WishlistItemSerializer
    filterset_fields = ["wishlist", "product"]


class ProductTagViewSet(viewsets.ModelViewSet):
    queryset = ProductTag.objects.all()
    serializer_class = ProductTagSerializer
    search_fields = ["name"]
    lookup_field = "slug"


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["product", "sku", "warehouse", "variant"]
    search_fields = ["product__name", "sku__number", "warehouse__name"]
    ordering_fields = ["quantity_available", "reorder_level", "last_restocked_at"]
    ordering = ["-last_restocked_at"]

    @action(detail=True, methods=["post"])
    def adjust_quantity(self, request, pk=None):
        """Adjust inventory quantity"""
        inventory = self.get_object()
        adjustment = request.data.get("adjustment", 0)
        adjustment_type = request.data.get("type", "available")  # available, reserved, incoming

        try:
            adjustment = int(adjustment)
        except ValueError:
            return Response({"error": "Invalid adjustment value"}, status=status.HTTP_400_BAD_REQUEST)

        if adjustment_type == "available":
            new_qty = inventory.quantity_available + adjustment
            if new_qty < 0:
                return Response({"error": "Cannot reduce below zero"}, status=status.HTTP_400_BAD_REQUEST)
            inventory.quantity_available = new_qty
        elif adjustment_type == "reserved":
            new_qty = inventory.quantity_reserved + adjustment
            if new_qty < 0:
                return Response({"error": "Cannot reduce below zero"}, status=status.HTTP_400_BAD_REQUEST)
            inventory.quantity_reserved = new_qty
        elif adjustment_type == "incoming":
            new_qty = inventory.quantity_incoming + adjustment
            if new_qty < 0:
                return Response({"error": "Cannot reduce below zero"}, status=status.HTTP_400_BAD_REQUEST)
            inventory.quantity_incoming = new_qty
        else:
            return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)

        inventory.save()
        serializer = self.get_serializer(inventory)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Get low stock items"""
        low_stock = Inventory.objects.filter(
            Q(quantity_available__lte=models.F("reorder_level")) | Q(quantity_available=0)
        )
        serializer = self.get_serializer(low_stock, many=True)
        return Response(serializer.data)
