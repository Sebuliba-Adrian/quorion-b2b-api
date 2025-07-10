from django.contrib import admin
from .models import Product, ProductSKU, PackagingType, PackagingUnit, ListPrice


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['name', 'brand_product_name', 'seller__name']


@admin.register(ProductSKU)
class ProductSKUAdmin(admin.ModelAdmin):
    list_display = ['number', 'product', 'distributor', 'kind', 'is_active']
    list_filter = ['kind', 'is_active']
    search_fields = ['number', 'product__name']


@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(PackagingUnit)
class PackagingUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(ListPrice)
class ListPriceAdmin(admin.ModelAdmin):
    list_display = ['sku', 'price', 'currency', 'is_active']
    list_filter = ['currency', 'is_active']
