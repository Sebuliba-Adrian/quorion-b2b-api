from django.contrib import admin

from .marketplace_models import (
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
from .models import ListPrice, PackagingType, PackagingUnit, Product, ProductSKU


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image_url", "alt_text", "is_primary", "order"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ["sku", "price_adjustment", "stock_quantity", "is_active"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "seller", "category", "status", "is_active", "is_featured", "view_count", "created_at"]
    list_filter = ["status", "is_active", "is_featured", "category"]
    search_fields = ["name", "brand_product_name", "seller__name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["tags"]
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ["view_count", "created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("seller", "category", "name", "slug", "brand_product_name")
        }),
        ("Description", {
            "fields": ("description", "short_description", "specifications")
        }),
        ("Settings", {
            "fields": ("status", "is_active", "is_featured", "tags")
        }),
        ("Statistics", {
            "fields": ("view_count", "created_at", "updated_at")
        }),
    )


@admin.register(ProductSKU)
class ProductSKUAdmin(admin.ModelAdmin):
    list_display = ["number", "product", "distributor", "kind", "is_active"]
    list_filter = ["kind", "is_active"]
    search_fields = ["number", "product__name"]


@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


@admin.register(PackagingUnit)
class PackagingUnitAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


@admin.register(ListPrice)
class ListPriceAdmin(admin.ModelAdmin):
    list_display = ["sku", "price", "currency", "is_active"]
    list_filter = ["currency", "is_active"]


# Marketplace Models


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "slug", "level", "is_active", "order"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["level"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "parent", "description")
        }),
        ("Settings", {
            "fields": ("is_active", "order", "image", "icon")
        }),
        ("Computed", {
            "fields": ("level",)
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "alt_text", "is_primary", "order", "created_at"]
    list_filter = ["is_primary", "created_at"]
    search_fields = ["product__name", "alt_text"]
    readonly_fields = ["created_at"]


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ["attribute", "value", "slug"]
    list_filter = ["attribute"]
    search_fields = ["value", "attribute__name", "slug"]


class ProductVariantAttributeInline(admin.TabularInline):
    model = ProductVariantAttribute
    extra = 1


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "sku", "price_adjustment", "stock_quantity", "is_active"]
    list_filter = ["is_active", "product"]
    search_fields = ["product__name", "sku__number"]
    inlines = [ProductVariantAttributeInline]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "buyer", "rating", "is_verified_purchase", "is_approved", "helpful_count", "created_at"]
    list_filter = ["rating", "is_verified_purchase", "is_approved", "created_at"]
    search_fields = ["product__name", "buyer__name", "review_text"]
    readonly_fields = ["helpful_count", "created_at", "updated_at"]
    actions = ["approve_reviews"]

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"


@admin.register(SellerRating)
class SellerRatingAdmin(admin.ModelAdmin):
    list_display = ["seller", "buyer", "rating", "communication_rating", "shipping_speed_rating", "product_quality_rating", "is_approved", "created_at"]
    list_filter = ["rating", "is_approved", "created_at"]
    search_fields = ["seller__name", "buyer__name"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["approve_ratings"]

    def approve_ratings(self, request, queryset):
        queryset.update(is_approved=True)
    approve_ratings.short_description = "Approve selected ratings"


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    fields = ["product", "variant", "notes", "added_at"]
    readonly_fields = ["added_at"]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["name", "buyer", "is_public", "is_active", "created_at"]
    list_filter = ["is_public", "is_active", "created_at"]
    search_fields = ["name", "buyer__name"]
    inlines = [WishlistItemInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["wishlist", "product", "variant", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["wishlist__name", "product__name"]
    readonly_fields = ["added_at"]


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ["product", "sku", "warehouse", "quantity_available", "quantity_reserved", "quantity_incoming", "reorder_level", "needs_reorder"]
    list_filter = ["warehouse", "last_restocked_at"]
    search_fields = ["product__name", "sku__number", "warehouse__name"]
    readonly_fields = ["needs_reorder", "last_restocked_at"]
    fieldsets = (
        ("Product Information", {
            "fields": ("product", "sku", "warehouse")
        }),
        ("Stock Levels", {
            "fields": ("quantity_available", "quantity_reserved", "quantity_incoming", "reorder_level")
        }),
        ("Status", {
            "fields": ("needs_reorder", "last_restocked_at")
        }),
    )
