"""
Serializers for marketplace-specific commerce models
"""

from rest_framework import serializers

from commerce.marketplace_models import (
    DirectCheckout,
    Notification,
    Payment,
    ProductView,
    PromoCode,
    SearchQuery,
)


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source="recipient.name", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_name",
            "notification_type",
            "title",
            "message",
            "link",
            "data",
            "is_read",
            "is_email_sent",
            "is_sms_sent",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_number",
            "payment_method",
            "amount",
            "currency",
            "status",
            "transaction_id",
            "payment_gateway",
            "gateway_response",
            "notes",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DirectCheckoutSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)
    shipping_address_display = serializers.SerializerMethodField()
    billing_address_display = serializers.SerializerMethodField()
    delivery_term_name = serializers.CharField(source="delivery_term.name", read_only=True)
    payment_term_name = serializers.CharField(source="payment_term.name", read_only=True, allow_null=True)
    order_number = serializers.CharField(source="order.number", read_only=True, allow_null=True)

    class Meta:
        model = DirectCheckout
        fields = [
            "id",
            "cart",
            "buyer",
            "buyer_name",
            "shipping_address",
            "shipping_address_display",
            "billing_address",
            "billing_address_display",
            "payment_method",
            "delivery_term",
            "delivery_term_name",
            "payment_term",
            "payment_term_name",
            "subtotal",
            "tax_amount",
            "shipping_cost",
            "discount_amount",
            "total_amount",
            "currency",
            "notes",
            "is_completed",
            "order",
            "order_number",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["id", "created_at", "completed_at"]

    def get_shipping_address_display(self, obj):
        """Get shipping address as formatted string"""
        addr = obj.shipping_address
        return f"{addr.address1}, {addr.city}, {addr.state} {addr.zip_code}, {addr.country}"

    def get_billing_address_display(self, obj):
        """Get billing address as formatted string"""
        addr = obj.billing_address
        return f"{addr.address1}, {addr.city}, {addr.state} {addr.zip_code}, {addr.country}"


class ProductViewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    viewer_name = serializers.CharField(source="viewer.name", read_only=True, allow_null=True)

    class Meta:
        model = ProductView
        fields = [
            "id",
            "product",
            "product_name",
            "viewer",
            "viewer_name",
            "session_id",
            "ip_address",
            "user_agent",
            "referrer",
            "viewed_at",
        ]
        read_only_fields = ["id", "viewed_at"]


class SearchQuerySerializer(serializers.ModelSerializer):
    searcher_name = serializers.CharField(source="searcher.name", read_only=True, allow_null=True)

    class Meta:
        model = SearchQuery
        fields = ["id", "query", "searcher", "searcher_name", "session_id", "results_count", "searched_at"]
        read_only_fields = ["id", "searched_at"]


class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = [
            "id",
            "code",
            "description",
            "discount_type",
            "discount_value",
            "min_purchase_amount",
            "max_discount_amount",
            "usage_limit",
            "usage_count",
            "per_user_limit",
            "valid_from",
            "valid_until",
            "is_active",
            "is_valid",
            "created_at",
        ]
        read_only_fields = ["id", "usage_count", "created_at"]

    def get_is_valid(self, obj):
        """Check if promo code is currently valid"""
        return obj.is_valid()
