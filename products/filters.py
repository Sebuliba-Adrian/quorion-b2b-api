"""
Product filters for advanced search and filtering
"""

from decimal import Decimal

import django_filters
from django.db.models import Avg, Q

from .marketplace_models import ProductCategory, ProductTag
from .models import Product, ProductSKU


class ProductFilter(django_filters.FilterSet):
    """Comprehensive product filtering for marketplace"""

    # Text search (searches name, description, brand)
    search = django_filters.CharFilter(method="filter_search", label="Search")

    # Category filtering (includes descendants)
    category = django_filters.ModelChoiceFilter(
        queryset=ProductCategory.objects.filter(is_active=True),
        method="filter_category",
        label="Category",
    )
    category_slug = django_filters.CharFilter(method="filter_category_slug", label="Category Slug")

    # Price range filtering (based on list prices)
    min_price = django_filters.NumberFilter(method="filter_min_price", label="Minimum Price")
    max_price = django_filters.NumberFilter(method="filter_max_price", label="Maximum Price")

    # Seller filtering
    seller = django_filters.UUIDFilter(field_name="seller__id")
    seller_name = django_filters.CharFilter(field_name="seller__name", lookup_expr="icontains")

    # Tags filtering
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=ProductTag.objects.all(), field_name="tags__slug", to_field_name="slug", conjoined=False
    )

    # Rating filtering
    min_rating = django_filters.NumberFilter(method="filter_min_rating", label="Minimum Rating")

    # Availability
    in_stock = django_filters.BooleanFilter(method="filter_in_stock", label="In Stock")

    # Featured products
    is_featured = django_filters.BooleanFilter(field_name="is_featured")

    # Status
    status = django_filters.ChoiceFilter(
        choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")]
    )

    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("created_at", "created_at"),
            ("view_count", "popularity"),
        ),
        field_labels={
            "name": "Name",
            "created_at": "Date Added",
            "view_count": "Popularity",
        },
    )

    class Meta:
        model = Product
        fields = ["status", "is_active", "is_featured", "seller"]

    def filter_search(self, queryset, name, value):
        """Full-text search across name, description, and brand"""
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(short_description__icontains=value)
            | Q(brand_product_name__icontains=value)
            | Q(slug__icontains=value)
        )

    def filter_category(self, queryset, name, value):
        """Filter by category including all descendants"""
        if not value:
            return queryset

        # Get all descendant categories
        category_ids = [value.id]
        descendants = value.get_descendants()
        category_ids.extend([cat.id for cat in descendants])

        return queryset.filter(category_id__in=category_ids)

    def filter_category_slug(self, queryset, name, value):
        """Filter by category slug"""
        if not value:
            return queryset

        try:
            category = ProductCategory.objects.get(slug=value)
            return self.filter_category(queryset, name, category)
        except ProductCategory.DoesNotExist:
            return queryset.none()

    def filter_min_price(self, queryset, name, value):
        """Filter by minimum price"""
        if not value:
            return queryset

        # Get products with list prices >= min_price
        from .models import ListPrice

        product_ids = (
            ListPrice.objects.filter(price__gte=Decimal(str(value)), is_active=True)
            .values_list("sku__product_id", flat=True)
            .distinct()
        )

        return queryset.filter(id__in=product_ids)

    def filter_max_price(self, queryset, name, value):
        """Filter by maximum price"""
        if not value:
            return queryset

        # Get products with list prices <= max_price
        from .models import ListPrice

        product_ids = (
            ListPrice.objects.filter(price__lte=Decimal(str(value)), is_active=True)
            .values_list("sku__product_id", flat=True)
            .distinct()
        )

        return queryset.filter(id__in=product_ids)

    def filter_min_rating(self, queryset, name, value):
        """Filter by minimum average rating"""
        if not value:
            return queryset

        from .marketplace_models import ProductReview

        # Get products with average rating >= min_rating
        product_ids = (
            ProductReview.objects.filter(is_approved=True)
            .values("product_id")
            .annotate(avg_rating=Avg("rating"))
            .filter(avg_rating__gte=Decimal(str(value)))
            .values_list("product_id", flat=True)
        )

        return queryset.filter(id__in=product_ids)

    def filter_in_stock(self, queryset, name, value):
        """Filter by stock availability"""
        if value is None:
            return queryset

        from .marketplace_models import Inventory

        if value:
            # Get products with available inventory
            product_ids = (
                Inventory.objects.filter(quantity_available__gt=0).values_list("product_id", flat=True).distinct()
            )
            return queryset.filter(id__in=product_ids)
        else:
            # Get products with no available inventory
            product_ids = (
                Inventory.objects.filter(quantity_available__gt=0).values_list("product_id", flat=True).distinct()
            )
            return queryset.exclude(id__in=product_ids)


class ProductSKUFilter(django_filters.FilterSet):
    """Filter for Product SKUs"""

    search = django_filters.CharFilter(method="filter_search", label="Search")
    product = django_filters.UUIDFilter(field_name="product__id")
    product_name = django_filters.CharFilter(field_name="product__name", lookup_expr="icontains")
    distributor = django_filters.UUIDFilter(field_name="distributor__id")
    buyer = django_filters.UUIDFilter(field_name="buyer__id")
    kind = django_filters.ChoiceFilter(
        choices=[
            ("master", "Master"),
            ("buyer_specific", "Buyer Specific"),
            ("distributor_specific", "Distributor Specific"),
        ]
    )
    min_price = django_filters.NumberFilter(method="filter_min_price")
    max_price = django_filters.NumberFilter(method="filter_max_price")

    class Meta:
        model = ProductSKU
        fields = ["is_active", "kind"]

    def filter_search(self, queryset, name, value):
        """Search by SKU number or name"""
        if not value:
            return queryset
        return queryset.filter(Q(number__icontains=value) | Q(name__icontains=value))

    def filter_min_price(self, queryset, name, value):
        """Filter by minimum list price"""
        if not value:
            return queryset

        from .models import ListPrice

        sku_ids = (
            ListPrice.objects.filter(price__gte=Decimal(str(value)), is_active=True)
            .values_list("sku_id", flat=True)
            .distinct()
        )
        return queryset.filter(id__in=sku_ids)

    def filter_max_price(self, queryset, name, value):
        """Filter by maximum list price"""
        if not value:
            return queryset

        from .models import ListPrice

        sku_ids = (
            ListPrice.objects.filter(price__lte=Decimal(str(value)), is_active=True)
            .values_list("sku_id", flat=True)
            .distinct()
        )
        return queryset.filter(id__in=sku_ids)
