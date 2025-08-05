from django.contrib import admin
from .models import (Lead, QuoteRequest, QuoteRequestDetail, PurchaseOrder,
                    PurchaseOrderDetail, PriceTier, ShipmentAdvice,
                    DeliveryTerm, PaymentTerm, PaymentMode)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller', 'buyer_company_name', 'buyer_email', 'status', 'created_at']
    list_filter = ['status', 'source']
    search_fields = ['buyer_email', 'buyer_company_name', 'seller__name']


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ['number', 'buyer', 'seller', 'status', 'total', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['number', 'buyer__name', 'seller__name']


@admin.register(QuoteRequestDetail)
class QuoteRequestDetailAdmin(admin.ModelAdmin):
    list_display = ['quote_request', 'product', 'sku', 'total_quantity', 'price_per_unit']
    list_filter = ['currency']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['number', 'buyer', 'seller', 'status', 'total', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['number', 'buyer__name', 'seller__name']


@admin.register(PurchaseOrderDetail)
class PurchaseOrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'sku', 'total_quantity', 'price_per_unit']


@admin.register(PriceTier)
class PriceTierAdmin(admin.ModelAdmin):
    list_display = ['product_sku', 'seller', 'buyer', 'price_per_uom', 'minimum_uom_quantity', 'is_active']
    list_filter = ['is_active', 'currency']


@admin.register(ShipmentAdvice)
class ShipmentAdviceAdmin(admin.ModelAdmin):
    list_display = ['order', 'carrier', 'carrier_number', 'estimated_time_of_arrival']


@admin.register(DeliveryTerm)
class DeliveryTermAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(PaymentMode)
class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
