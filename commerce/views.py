"""
Views for commerce: Carts, Leads, Quotes, Orders, Shipping
"""

import random
import string
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.permissions import (
    CanAccessLead,
    CanAccessOrder,
    CanAccessQuote,
    IsBuyer,
    IsBuyerOrSeller,
    IsSeller,
    IsSellerOrDistributor,
    IsTenantOwner,
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
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CustomerSerializer,
    DeliveryTermSerializer,
    LeadSerializer,
    PaymentModeSerializer,
    PaymentTermSerializer,
    PriceTierSerializer,
    PurchaseOrderDetailSerializer,
    PurchaseOrderSerializer,
    QuoteRequestDetailSerializer,
    QuoteRequestSerializer,
    ShipmentAdviceSerializer,
)


def generate_quote_number():
    """Generate unique quote number"""
    while True:
        number = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not QuoteRequest.objects.filter(number=number).exists():
            return number


def generate_order_number():
    """Generate unique order number"""
    while True:
        number = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not PurchaseOrder.objects.filter(number=number).exists():
            return number


class CustomerViewSet(viewsets.ModelViewSet):
    """API endpoint for managing customers"""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ["tenant", "email", "is_active"]


class CartViewSet(viewsets.ModelViewSet):
    """API endpoint for managing shopping carts"""

    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    filterset_fields = ["buyer", "is_active"]

    def get_permissions(self):
        """
        Anonymous users can create carts and add items (guest shopping)
        convert_to_lead is for lead generation and can be done by anyone
        Other operations require appropriate authentication
        """
        from rest_framework.permissions import AllowAny

        # Allow anonymous cart creation, item management, and lead conversion
        if self.action in ['create', 'list', 'retrieve', 'add_item', 'remove_item', 'add_bulk_items', 'clear', 'validate', 'convert_to_lead']:
            return [AllowAny()]
        # Authenticated users can clone/merge carts
        elif self.action in ['clone', 'merge']:
            return [IsAuthenticated()]
        # Other actions require authentication
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        """Add or update item in cart"""
        cart = self.get_object()
        product_id = request.data.get("product")
        quantity = request.data.get("quantity")
        unit_price = request.data.get("unit_price")
        notes = request.data.get("notes", "")

        if not all([product_id, quantity, unit_price]):
            return Response(
                {"error": "product, quantity, and unit_price are required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Convert to Decimal
            quantity = Decimal(str(quantity))
            unit_price = Decimal(str(unit_price))

            # Validate quantity and price
            if quantity <= 0:
                return Response({"error": "Quantity must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
            if unit_price < 0:
                return Response({"error": "Unit price cannot be negative"}, status=status.HTTP_400_BAD_REQUEST)

            existing_item = CartItem.objects.filter(cart=cart, product_id=product_id, deleted_at__isnull=True).first()

            if existing_item:
                existing_item.quantity = quantity
                existing_item.unit_price = unit_price
                existing_item.notes = notes
                existing_item.save()
                serializer = CartItemSerializer(existing_item)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                cart_item = CartItem.objects.create(
                    cart=cart, product_id=product_id, quantity=quantity, unit_price=unit_price, notes=notes
                )
                serializer = CartItemSerializer(cart_item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def remove_item(self, request, pk=None):
        """Remove item from cart (soft delete)"""
        cart = self.get_object()
        item_id = request.data.get("item_id")

        if not item_id:
            return Response({"error": "item_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart, deleted_at__isnull=True)
            cart_item.soft_delete()
            return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        """Clear all items from cart"""
        cart = self.get_object()
        cart.clear()
        return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def convert_to_lead(self, request, pk=None):
        """Convert cart to a lead"""
        cart = self.get_object()

        if cart.total_items == 0:
            return Response({"error": "Cannot convert empty cart to lead"}, status=status.HTTP_400_BAD_REQUEST)

        seller_id = request.data.get("seller")
        buyer_first_name = request.data.get("buyer_first_name")
        buyer_last_name = request.data.get("buyer_last_name")
        buyer_email = request.data.get("buyer_email")

        if not all([seller_id, buyer_first_name, buyer_last_name, buyer_email]):
            return Response(
                {"error": "seller, buyer_first_name, buyer_last_name, and buyer_email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = Lead.objects.create(
            seller_id=seller_id,
            cart=cart,
            buyer_first_name=buyer_first_name,
            buyer_last_name=buyer_last_name,
            buyer_email=buyer_email,
            buyer_phone=request.data.get("buyer_phone", ""),
            buyer_company_name=request.data.get("buyer_company_name", ""),
        )
        lead.create()
        lead.save()

        cart.is_active = False
        cart.save()

        return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """Clone cart for reordering"""
        from tenants.models import Tenant

        cart = self.get_object()
        buyer_id = request.data.get("buyer")
        customer_id = request.data.get("customer")

        buyer = None
        customer = None

        if buyer_id:
            try:
                buyer = Tenant.objects.get(id=buyer_id)
            except Tenant.DoesNotExist:
                pass

        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                pass

        new_cart = cart.clone(buyer=buyer, customer=customer)
        return Response(CartSerializer(new_cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def merge(self, request, pk=None):
        """Merge another cart into this one"""
        cart = self.get_object()
        other_cart_id = request.data.get("other_cart_id")

        if not other_cart_id:
            return Response({"error": "other_cart_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other_cart = Cart.objects.get(id=other_cart_id)
            cart.merge_with(other_cart)
            return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def validate(self, request, pk=None):
        """Validate cart"""
        cart = self.get_object()
        errors = cart.validate_cart()

        if errors:
            return Response({"valid": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"valid": True, "errors": []}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def add_bulk_items(self, request, pk=None):
        """Add multiple items to cart at once"""
        cart = self.get_object()
        items_data = request.data.get("items", [])

        if not items_data:
            return Response({"error": "items array is required"}, status=status.HTTP_400_BAD_REQUEST)

        added_items = []
        for item_data in items_data:
            product_id = item_data.get("product")
            quantity = item_data.get("quantity")
            unit_price = item_data.get("unit_price")

            if not all([product_id, quantity, unit_price]):
                continue

            existing = cart.items.filter(product_id=product_id, deleted_at__isnull=True).first()
            if existing:
                existing.quantity += Decimal(str(quantity))
                existing.save()
                added_items.append(existing)
            else:
                item = CartItem.objects.create(
                    cart=cart,
                    product_id=product_id,
                    quantity=Decimal(str(quantity)),
                    unit_price=Decimal(str(unit_price)),
                    notes=item_data.get("notes", ""),
                )
                added_items.append(item)

        return Response(CartItemSerializer(added_items, many=True).data, status=status.HTTP_201_CREATED)


class CartItemViewSet(viewsets.ModelViewSet):
    """API endpoint for managing cart items"""

    queryset = CartItem.objects.filter(deleted_at__isnull=True)
    serializer_class = CartItemSerializer
    filterset_fields = ["cart", "product"]


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filterset_fields = ["seller", "status", "customer"]

    def get_permissions(self):
        """
        Sellers and distributors can create/manage leads
        All authenticated users can list/retrieve leads they have access to
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSellerOrDistributor()]
        elif self.action in ['list', 'retrieve']:
            return [CanAccessLead()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def create_lead(self, request, pk=None):
        """Create new lead"""
        lead = self.get_object()
        lead.create()
        lead.save()
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def convert_to_customer(self, request, pk=None):
        """Convert lead to customer"""
        lead = self.get_object()
        credit_limit = request.data.get("credit_limit", "0.00")
        payment_terms_days = request.data.get("payment_terms_days", 30)

        customer = lead.convert_to_customer(
            credit_limit=Decimal(str(credit_limit)), payment_terms_days=int(payment_terms_days)
        )

        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Convert lead to quote"""
        lead = self.get_object()
        lead.convert()
        lead.save()
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def forward_to_distributor(self, request, pk=None):
        """Forward lead to distributor"""
        lead = self.get_object()
        distributor_id = request.data.get("distributor_id")
        if not distributor_id:
            return Response({"error": "distributor_id required"}, status=status.HTTP_400_BAD_REQUEST)

        from tenants.models import Tenant

        try:
            distributor = Tenant.objects.get(id=distributor_id, type="distributor")
        except Tenant.DoesNotExist:
            return Response({"error": "Distributor not found"}, status=status.HTTP_404_NOT_FOUND)

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

        return Response(
            {"parent_lead": LeadSerializer(lead).data, "child_lead": LeadSerializer(child_lead).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def accept_by_distributor(self, request, pk=None):
        """Distributor accepts lead"""
        lead = self.get_object()
        lead.accept_by_distributor()
        lead.save()
        # Parent lead should already be in forwarded state
        if lead.parent_lead and lead.parent_lead.status == "forwarded":
            # Parent lead stays in forwarded state when child is accepted
            pass
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def reject_by_distributor(self, request, pk=None):
        """Distributor rejects lead"""
        lead = self.get_object()
        lead.reject_by_distributor()
        lead.save()
        return Response(LeadSerializer(lead).data)


class QuoteRequestViewSet(viewsets.ModelViewSet):
    queryset = QuoteRequest.objects.all()
    serializer_class = QuoteRequestSerializer
    filterset_fields = ["buyer", "seller", "status", "is_active"]

    def get_permissions(self):
        """
        Buyers and sellers can create/manage quotes they're involved in
        """
        if self.action in ['create']:
            return [IsBuyerOrSeller()]
        elif self.action in ['list', 'retrieve']:
            return [CanAccessQuote()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [CanAccessQuote()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        quote = serializer.save()
        quote.number = generate_quote_number()
        quote.create_quote()
        quote.save()

    @action(detail=True, methods=["post"])
    def buyer_requests(self, request, pk=None):
        """Buyer submits quote request"""
        quote = self.get_object()
        quote.buyer_requests()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"])
    def seller_responds(self, request, pk=None):
        """Seller responds with pricing"""
        quote = self.get_object()

        # Update items with prices
        items_data = request.data.get("items", [])
        for item_data in items_data:
            item_id = item_data.get("id")
            price_per_unit = item_data.get("price_per_unit")

            if item_id and price_per_unit:
                try:
                    item = QuoteRequestDetail.objects.get(id=item_id, quote_request=quote)
                    item.price_per_unit = price_per_unit
                    item.save()
                except QuoteRequestDetail.DoesNotExist:
                    pass

        # Update shipping cost if provided
        if "shipping_cost" in request.data:
            from decimal import Decimal

            quote.shipping_cost = Decimal(str(request.data["shipping_cost"]))
            quote.save()  # Save before state transition

        quote.seller_responds()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"])
    def seller_modifies(self, request, pk=None):
        """Seller modifies quote"""
        quote = self.get_object()
        quote.seller_modifies()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"])
    def buyer_responds(self, request, pk=None):
        """Buyer requests modification"""
        quote = self.get_object()
        quote.buyer_responds()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"])
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

        return Response(
            {"quote": QuoteRequestSerializer(quote).data, "order": PurchaseOrderSerializer(order).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel quote"""
        quote = self.get_object()
        quote.cancel()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"])
    def seller_declines(self, request, pk=None):
        """Seller declines quote"""
        quote = self.get_object()
        quote.seller_declines()
        quote.save()
        return Response(QuoteRequestSerializer(quote).data)


class QuoteRequestDetailViewSet(viewsets.ModelViewSet):
    queryset = QuoteRequestDetail.objects.all()
    serializer_class = QuoteRequestDetailSerializer
    filterset_fields = ["quote_request", "product", "sku"]

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
    filterset_fields = ["buyer", "seller", "status", "is_active"]

    def get_permissions(self):
        """
        Buyers and sellers can create/manage orders they're involved in
        """
        if self.action in ['create']:
            return [IsBuyerOrSeller()]
        elif self.action in ['list', 'retrieve']:
            return [CanAccessOrder()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [CanAccessOrder()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        order = serializer.save()
        order.number = generate_order_number()
        order.create_order()
        order.save()

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Seller accepts order"""
        order = self.get_object()
        order.accept()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def make_in_progress(self, request, pk=None):
        """Start processing order"""
        order = self.get_object()
        order.make_in_progress()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def invoice(self, request, pk=None):
        """Generate invoice"""
        order = self.get_object()
        order.invoice()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def ship_order(self, request, pk=None):
        """Ship order"""
        order = self.get_object()
        order.ship_order()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def receive_payment(self, request, pk=None):
        """Receive payment"""
        order = self.get_object()
        order.receive_payment()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete order"""
        order = self.get_object()
        order.complete()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()
        order.cancel()
        order.save()
        return Response(PurchaseOrderSerializer(order).data)


class PriceTierViewSet(viewsets.ModelViewSet):
    queryset = PriceTier.objects.all()
    serializer_class = PriceTierSerializer
    filterset_fields = ["seller", "buyer", "product_sku", "is_active"]

    def get_permissions(self):
        """
        Sellers can create/manage price tiers
        Buyers and sellers can view tiers
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSeller()]
        return [IsBuyerOrSeller()]


class PurchaseOrderDetailViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderDetail.objects.all()
    serializer_class = PurchaseOrderDetailSerializer
    filterset_fields = ["order", "product", "sku"]


class ShipmentAdviceViewSet(viewsets.ModelViewSet):
    queryset = ShipmentAdvice.objects.all()
    serializer_class = ShipmentAdviceSerializer
    filterset_fields = ["order"]


class DeliveryTermViewSet(viewsets.ModelViewSet):
    queryset = DeliveryTerm.objects.all()
    serializer_class = DeliveryTermSerializer


class PaymentTermViewSet(viewsets.ModelViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer


class PaymentModeViewSet(viewsets.ModelViewSet):
    queryset = PaymentMode.objects.all()
    serializer_class = PaymentModeSerializer
