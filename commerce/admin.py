from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Customer,
    DeliveryTerm,
    Lead,
    PaymentMode,
    PaymentTerm,
    PriceTier,
    PurchaseOrder,
    PurchaseOrderDetail,
    QuoteRequest,
    QuoteRequestDetail,
    ShipmentAdvice,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "company_name", "tenant", "credit_limit", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["first_name", "last_name", "email", "company_name", "tenant__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "buyer", "is_active", "total_items", "subtotal", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["buyer__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "product", "quantity", "unit_price", "total_price", "deleted_at"]
    list_filter = ["deleted_at", "created_at"]
    search_fields = ["product__name", "cart__buyer__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["id", "seller", "buyer_company_name", "buyer_email", "status", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["buyer_email", "buyer_company_name", "seller__name"]


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ["number", "buyer", "seller", "status", "total", "created_at"]
    list_filter = ["status", "is_active"]
    search_fields = ["number", "buyer__name", "seller__name"]


@admin.register(QuoteRequestDetail)
class QuoteRequestDetailAdmin(admin.ModelAdmin):
    list_display = ["quote_request", "product", "sku", "total_quantity", "price_per_unit"]
    list_filter = ["currency"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["number", "buyer", "seller", "status", "total", "created_at"]
    list_filter = ["status", "is_active"]
    search_fields = ["number", "buyer__name", "seller__name"]


@admin.register(PurchaseOrderDetail)
class PurchaseOrderDetailAdmin(admin.ModelAdmin):
    list_display = ["order", "product", "sku", "total_quantity", "price_per_unit"]


@admin.register(PriceTier)
class PriceTierAdmin(admin.ModelAdmin):
    list_display = ["product_sku", "seller", "buyer", "price_per_uom", "minimum_uom_quantity", "is_active"]
    list_filter = ["is_active", "currency"]


@admin.register(ShipmentAdvice)
class ShipmentAdviceAdmin(admin.ModelAdmin):
    list_display = ["order", "carrier", "carrier_number", "estimated_time_of_arrival"]


@admin.register(DeliveryTerm)
class DeliveryTermAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


@admin.register(PaymentMode)
class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
