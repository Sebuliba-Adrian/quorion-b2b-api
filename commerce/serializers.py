"""
Serializers for commerce models
"""
from rest_framework import serializers
from .models import (Customer, Cart, CartItem, Lead, QuoteRequest, QuoteRequestDetail, PurchaseOrder,
                    PurchaseOrderDetail, PriceTier, ShipmentAdvice,
                    DeliveryTerm, PaymentTerm, PaymentMode)
from tenants.serializers import TenantSerializer, TenantAddressSerializer
from products.serializers import ProductSerializer, ProductSKUSerializer


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for customers"""
    full_name = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'tenant', 'tenant_name', 'first_name', 'last_name', 'full_name',
                 'email', 'phone', 'company_name', 'tax_id', 'credit_limit',
                 'payment_terms_days', 'is_active', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_name', 'product_sku', 'quantity',
                 'unit_price', 'total_price', 'notes', 'deleted_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'deleted_at', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping carts"""
    buyer_name = serializers.CharField(source='buyer.name', read_only=True, allow_null=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True, allow_null=True)
    items = serializers.SerializerMethodField()
    total_items = serializers.IntegerField(read_only=True)
    total_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_anonymous = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'buyer', 'buyer_name', 'customer', 'customer_name', 'session_key',
                 'is_active', 'expires_at', 'name', 'is_anonymous', 'is_expired',
                 'items', 'total_items', 'total_quantity', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_items(self, obj):
        """Get only active (non-deleted) items"""
        active_items = obj.items.filter(deleted_at__isnull=True)
        return CartItemSerializer(active_items, many=True).data


class DeliveryTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryTerm
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class PaymentModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMode
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class PriceTierSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    product_sku_number = serializers.CharField(source='product_sku.number', read_only=True)

    class Meta:
        model = PriceTier
        fields = ['id', 'seller', 'seller_name', 'buyer', 'buyer_name', 'destination',
                 'product_sku', 'product_sku_number', 'delivery_term', 'payment_term',
                 'minimum_uom_quantity', 'price_per_uom', 'currency',
                 'valid_from_date', 'valid_to_date', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeadSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    parent_lead_id = serializers.UUIDField(source='parent_lead.id', read_only=True, allow_null=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True, allow_null=True)

    class Meta:
        model = Lead
        fields = ['id', 'seller', 'seller_name', 'cart', 'customer', 'customer_name',
                 'buyer_first_name', 'buyer_last_name', 'buyer_email', 'buyer_phone',
                 'buyer_company_name', 'status', 'parent_lead', 'parent_lead_id',
                 'source', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class QuoteRequestDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku_number = serializers.CharField(source='sku.number', read_only=True, allow_null=True)
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteRequestDetail
        fields = ['id', 'quote_request', 'product', 'product_name', 'sku', 'sku_number',
                 'requested_sku', 'no_of_units', 'total_quantity', 'price_per_unit',
                 'currency', 'total_value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuoteRequestSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    items = QuoteRequestDetailSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteRequest
        fields = ['id', 'buyer', 'buyer_name', 'seller', 'seller_name', 'lead', 'number',
                 'status', 'warehouse', 'delivery_term', 'payment_term', 'payment_mode',
                 'shipping_cost', 'currency', 'is_active', 'items', 'subtotal', 'total',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'number', 'status', 'created_at', 'updated_at']


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku_number = serializers.CharField(source='sku.number', read_only=True)
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrderDetail
        fields = ['id', 'order', 'product', 'product_name', 'sku', 'sku_number',
                 'no_of_units', 'total_quantity', 'price_per_unit', 'currency',
                 'total_value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShipmentAdviceSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.number', read_only=True)

    class Meta:
        model = ShipmentAdvice
        fields = ['id', 'order', 'order_number', 'estimated_time_of_dispatch',
                 'estimated_time_of_arrival', 'carrier', 'carrier_number',
                 'vessel_name', 'port_of_loading', 'port_of_discharge',
                 'additional_comments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    items = PurchaseOrderDetailSerializer(many=True, read_only=True)
    shipments = ShipmentAdviceSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'buyer', 'buyer_name', 'seller', 'seller_name', 'quote_request',
                 'number', 'status', 'warehouse', 'delivery_term', 'payment_term',
                 'payment_mode', 'shipping_cost', 'currency', 'is_active', 'items',
                 'shipments', 'subtotal', 'total', 'created_at', 'updated_at']
        read_only_fields = ['id', 'number', 'status', 'created_at', 'updated_at']

