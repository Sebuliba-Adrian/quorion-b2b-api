"""
Serializers for commerce models
"""
from rest_framework import serializers
from .models import (Lead, QuoteRequest, QuoteRequestDetail, PurchaseOrder, 
                    PurchaseOrderDetail, PriceTier, ShipmentAdvice,
                    DeliveryTerm, PaymentTerm, PaymentMode)
from tenants.serializers import TenantSerializer, TenantAddressSerializer
from products.serializers import ProductSerializer, ProductSKUSerializer


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

    class Meta:
        model = Lead
        fields = ['id', 'seller', 'seller_name', 'buyer_first_name', 'buyer_last_name',
                 'buyer_email', 'buyer_phone', 'buyer_company_name', 'status', 'parent_lead',
                 'parent_lead_id', 'source', 'created_at', 'updated_at']
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

