from django.contrib import admin

from .marketplace_models import (
    DirectCheckout,
    Notification,
    Payment,
    ProductView,
    PromoCode,
    SearchQuery,
)
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


# Marketplace Models


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "notification_type", "title", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["recipient__name", "title", "message"]
    readonly_fields = ["created_at"]
    actions = ["mark_as_read"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected notifications as read"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "payment_method", "amount", "currency", "status", "paid_at", "created_at"]
    list_filter = ["payment_method", "status", "currency", "created_at"]
    search_fields = ["order__number", "transaction_id", "gateway_payment_id"]
    readonly_fields = ["created_at", "paid_at"]
    fieldsets = (
        ("Order Information", {
            "fields": ("order",)
        }),
        ("Payment Details", {
            "fields": ("payment_method", "amount", "currency", "status")
        }),
        ("Gateway Information", {
            "fields": ("gateway_payment_id", "gateway_response", "transaction_id")
        }),
        ("Timestamps", {
            "fields": ("created_at", "paid_at")
        }),
    )


@admin.register(DirectCheckout)
class DirectCheckoutAdmin(admin.ModelAdmin):
    list_display = ["buyer", "cart", "payment_method", "total_amount", "is_completed", "created_at"]
    list_filter = ["payment_method", "is_completed", "created_at"]
    search_fields = ["buyer__name", "shipping_address__address_line_1"]
    readonly_fields = ["created_at", "completed_at", "subtotal", "total_amount"]
    fieldsets = (
        ("Buyer Information", {
            "fields": ("cart", "buyer", "shipping_address", "billing_address")
        }),
        ("Payment & Delivery", {
            "fields": ("payment_method", "delivery_term", "payment_term")
        }),
        ("Pricing", {
            "fields": ("subtotal", "tax_amount", "shipping_cost", "discount_amount", "total_amount", "currency")
        }),
        ("Status", {
            "fields": ("is_completed", "completed_at", "order")
        }),
        ("Additional", {
            "fields": ("special_instructions", "created_at")
        }),
    )


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ["product", "viewer", "ip_address", "user_agent_short", "viewed_at"]
    list_filter = ["viewed_at"]
    search_fields = ["product__name", "viewer__name", "ip_address"]
    readonly_fields = ["viewed_at"]
    date_hierarchy = "viewed_at"

    def user_agent_short(self, obj):
        if obj.user_agent:
            return obj.user_agent[:50] + "..." if len(obj.user_agent) > 50 else obj.user_agent
        return "-"
    user_agent_short.short_description = "User Agent"


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ["query", "searcher", "results_count", "searched_at"]
    list_filter = ["searched_at"]
    search_fields = ["query", "searcher__name", "filters"]
    readonly_fields = ["searched_at"]
    date_hierarchy = "searched_at"


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "is_active", "valid_from", "valid_until", "usage_count", "usage_limit"]
    list_filter = ["discount_type", "is_active", "valid_from", "valid_until"]
    search_fields = ["code", "description"]
    readonly_fields = ["usage_count"]
    fieldsets = (
        ("Code Information", {
            "fields": ("code", "description")
        }),
        ("Discount Configuration", {
            "fields": ("discount_type", "discount_value", "max_discount_amount", "min_purchase_amount")
        }),
        ("Validity", {
            "fields": ("valid_from", "valid_until", "is_active")
        }),
        ("Usage Limits", {
            "fields": ("usage_limit", "per_user_limit", "usage_count")
        }),
    )
