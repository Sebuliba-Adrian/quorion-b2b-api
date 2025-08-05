"""
Views for commerce: Leads, Quotes, Orders, Shipping
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import random
import string

from .models import (Lead, QuoteRequest, QuoteRequestDetail, PurchaseOrder,
                    PurchaseOrderDetail, PriceTier, ShipmentAdvice,
                    DeliveryTerm, PaymentTerm, PaymentMode)
from .serializers import (LeadSerializer, QuoteRequestSerializer, QuoteRequestDetailSerializer,
                         PurchaseOrderSerializer, PurchaseOrderDetailSerializer,
                         PriceTierSerializer, ShipmentAdviceSerializer,
                         DeliveryTermSerializer, PaymentTermSerializer, PaymentModeSerializer)


def generate_quote_number():
    """Generate unique quote number"""
    while True:
        number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not QuoteRequest.objects.filter(number=number).exists():
            return number


def generate_order_number():
    """Generate unique order number"""
    while True:
        number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not PurchaseOrder.objects.filter(number=number).exists():
            return number


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filterset_fields = ['seller', 'status']

    @action(detail=True, methods=['post'])
    def create_lead(self, request, pk=None):
        """Create new lead"""
        lead = self.get_object()
        lead.create()
        lead.save()
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """Convert lead to quote"""
        lead = self.get_object()
        lead.convert()
        lead.save()
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=['post'])
    def forward_to_distributor(self, request, pk=None):
        """Forward lead to distributor"""
        lead = self.get_object()
        distributor_id = request.data.get('distributor_id')
        if not distributor_id:
            return Response({'error': 'distributor_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        from tenants.models import Tenant
        try:
            distributor = Tenant.objects.get(id=distributor_id, type='distributor')
        except Tenant.DoesNotExist:
            return Response({'error': 'Distributor not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        lead.forward_to_distributor()
        lead.save()
        
        # Create child lead for distributor
        child_lead = Lead.objects.create(
            seller=distributor,
            buyer_first_name=lead.buyer_first_name,
            buyer_last_name=lead.buyer_last_name,
            buyer_email=lead.buyer_email,
            buyer_phone=lead.buyer_phone,
            buyer_company_name=lead.buyer_company_name,
            parent_lead=lead,
            source=lead.source,
        )
        child_lead.create()
        child_lead.save()
        
        return Response({
            'parent_lead': LeadSerializer(lead).data,
            'child_lead': LeadSerializer(child_lead).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def accept_by_distributor(self, request, pk=None):
        """Distributor accepts lead"""
        lead = self.get_object()
        lead.accept_by_distributor()
        lead.save()
        # Parent lead should already be in forwarded state
        if lead.parent_lead and lead.parent_lead.status == 'forwarded':
            # Parent lead stays in forwarded state when child is accepted
            pass
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=['post'])
    def reject_by_distributor(self, request, pk=None):
        """Distributor rejects lead"""
        lead = self.get_object()
        lead.reject_by_distributor()
        lead.save()
        return Response(LeadSerializer(lead).data)


class QuoteRequestViewSet(viewsets.ModelViewSet):
    queryset = QuoteRequest.objects.all()
    serializer_class = QuoteRequestSerializer
    filterset_fields = ['buyer', 'seller', 'status', 'is_active']

    def perform_create(self, serializer):
        quote = serializer.save()
        quote.number = generate_quote_number()
        quote.create_quote()
        quote.save()

    @action(detail=True, methods=['post'])
    def buyer_requests(self, request, pk=None):
        """Buyer submits quote request"""
        quote = self.get_object()
        quote.buyer_requests()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=['post'])
    def seller_responds(self, request, pk=None):
        """Seller responds with pricing"""
        quote = self.get_object()
        
        # Update items with prices
        items_data = request.data.get('items', [])
        for item_data in items_data:
            item_id = item_data.get('id')
            price_per_unit = item_data.get('price_per_unit')
            
            if item_id and price_per_unit:
                try:
                    item = QuoteRequestDetail.objects.get(id=item_id, quote_request=quote)
                    item.price_per_unit = price_per_unit
                    item.save()
                except QuoteRequestDetail.DoesNotExist:
                    pass
        
        # Update shipping cost if provided
        if 'shipping_cost' in request.data:
            from decimal import Decimal
            quote.shipping_cost = Decimal(str(request.data['shipping_cost']))
            quote.save()  # Save before state transition
        
        quote.seller_responds()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=['post'])
    def seller_modifies(self, request, pk=None):
        """Seller modifies quote"""
        quote = self.get_object()
        quote.seller_modifies()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=['post'])
    def buyer_responds(self, request, pk=None):
        """Buyer requests modification"""
        quote = self.get_object()
        quote.buyer_responds()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def buyer_accepts(self, request, pk=None):
        """Buyer accepts quote - creates purchase order"""
        quote = self.get_object()
        quote.buyer_accepts()
        quote.save()
        
        # Create purchase order
        order = PurchaseOrder.objects.create(
            buyer=quote.buyer,
            seller=quote.seller,
            quote_request=quote,
            number=generate_order_number(),
            warehouse=quote.warehouse,
            delivery_term=quote.delivery_term,
            payment_term=quote.payment_term,
            payment_mode=quote.payment_mode,
            shipping_cost=quote.shipping_cost,
            currency=quote.currency,
        )
        order.create_order()
        order.save()
        
        # Copy items from quote to order
        for quote_item in quote.items.all():
            PurchaseOrderDetail.objects.create(
                order=order,
                product=quote_item.product,
                sku=quote_item.sku or quote_item.requested_sku,
                no_of_units=quote_item.no_of_units,
                total_quantity=quote_item.total_quantity,
                price_per_unit=quote_item.price_per_unit,
                currency=quote_item.currency,
            )
        
        return Response({
            'quote': QuoteRequestSerializer(quote).data,
            'order': PurchaseOrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel quote"""
        quote = self.get_object()
        quote.cancel()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=['post'])
    def seller_declines(self, request, pk=None):
        """Seller declines quote"""
        quote = self.get_object()
        quote.seller_declines()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)


class QuoteRequestDetailViewSet(viewsets.ModelViewSet):
    queryset = QuoteRequestDetail.objects.all()
    serializer_class = QuoteRequestDetailSerializer
    filterset_fields = ['quote_request', 'product', 'sku']

    def perform_create(self, serializer):
        item = serializer.save()
        # Auto-resolve price from price tier if not provided
        if not item.price_per_unit:
            price = item.get_price_from_tier()
            if price:
                item.price_per_unit = price
                item.save()


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ['buyer', 'seller', 'status', 'is_active']

    def perform_create(self, serializer):
        order = serializer.save()
        order.number = generate_order_number()
        order.create_order()
        order.save()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Seller accepts order"""
        order = self.get_object()
        order.accept()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def make_in_progress(self, request, pk=None):
        """Start processing order"""
        order = self.get_object()
        order.make_in_progress()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def invoice(self, request, pk=None):
        """Generate invoice"""
        order = self.get_object()
        order.invoice()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def ship_order(self, request, pk=None):
        """Ship order"""
        order = self.get_object()
        order.ship_order()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def receive_payment(self, request, pk=None):
        """Receive payment"""
        order = self.get_object()
        order.receive_payment()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete order"""
        order = self.get_object()
        order.complete()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()
        order.cancel()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)


class PriceTierViewSet(viewsets.ModelViewSet):
    queryset = PriceTier.objects.all()
    serializer_class = PriceTierSerializer
    filterset_fields = ['seller', 'buyer', 'product_sku', 'is_active']


class PurchaseOrderDetailViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderDetail.objects.all()
    serializer_class = PurchaseOrderDetailSerializer
    filterset_fields = ['order', 'product', 'sku']


class ShipmentAdviceViewSet(viewsets.ModelViewSet):
    queryset = ShipmentAdvice.objects.all()
    serializer_class = ShipmentAdviceSerializer
    filterset_fields = ['order']


class DeliveryTermViewSet(viewsets.ModelViewSet):
    queryset = DeliveryTerm.objects.all()
    serializer_class = DeliveryTermSerializer


class PaymentTermViewSet(viewsets.ModelViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer


class PaymentModeViewSet(viewsets.ModelViewSet):
    queryset = PaymentMode.objects.all()
    serializer_class = PaymentModeSerializer
