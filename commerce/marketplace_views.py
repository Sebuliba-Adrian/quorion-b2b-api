"""
ViewSets for marketplace-specific commerce features
"""

from decimal import Decimal

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from commerce.marketplace_models import (
    DirectCheckout,
    Notification,
    Payment,
    ProductView,
    PromoCode,
    SearchQuery,
)
from commerce.marketplace_serializers import (
    DirectCheckoutSerializer,
    NotificationSerializer,
    PaymentSerializer,
    ProductViewSerializer,
    PromoCodeSerializer,
    SearchQuerySerializer,
)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filterset_fields = ["recipient", "notification_type", "is_read"]

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read for a recipient"""
        recipient_id = request.data.get("recipient_id")
        if not recipient_id:
            return Response({"error": "recipient_id required"}, status=status.HTTP_400_BAD_REQUEST)

        Notification.objects.filter(recipient_id=recipient_id, is_read=False).update(is_read=True)
        return Response({"message": "All notifications marked as read"})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get unread notification count for a recipient"""
        recipient_id = request.query_params.get("recipient_id")
        if not recipient_id:
            return Response({"error": "recipient_id required"}, status=status.HTTP_400_BAD_REQUEST)

        count = Notification.objects.filter(recipient_id=recipient_id, is_read=False).count()
        return Response({"unread_count": count})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_fields = ["order", "payment_method", "status"]

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Process payment (mock - integrate with Stripe/PayPal)"""
        payment = self.get_object()

        if payment.status == "completed":
            return Response({"error": "Payment already completed"}, status=status.HTTP_400_BAD_REQUEST)

        # This is where you'd integrate with Stripe/PayPal
        # For now, we'll mark it as completed
        payment.status = "completed"
        payment.paid_at = timezone.now()
        payment.save()

        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """Refund payment"""
        payment = self.get_object()

        if payment.status != "completed":
            return Response({"error": "Can only refund completed payments"}, status=status.HTTP_400_BAD_REQUEST)

        # This is where you'd integrate with payment gateway refund API
        payment.status = "refunded"
        payment.save()

        serializer = self.get_serializer(payment)
        return Response(serializer.data)


class DirectCheckoutViewSet(viewsets.ModelViewSet):
    queryset = DirectCheckout.objects.all()
    serializer_class = DirectCheckoutSerializer
    filterset_fields = ["buyer", "is_completed"]

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        """Calculate checkout totals"""
        checkout = self.get_object()
        checkout.calculate_totals()
        serializer = self.get_serializer(checkout)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def apply_promo_code(self, request, pk=None):
        """Apply promo code to checkout"""
        checkout = self.get_object()
        promo_code = request.data.get("promo_code")

        if not promo_code:
            return Response({"error": "promo_code required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            promo = PromoCode.objects.get(code=promo_code)
        except PromoCode.DoesNotExist:
            return Response({"error": "Invalid promo code"}, status=status.HTTP_404_NOT_FOUND)

        if not promo.is_valid():
            return Response({"error": "Promo code is not valid or expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        discount = promo.calculate_discount(checkout.subtotal)
        checkout.discount_amount = discount
        checkout.calculate_totals()
        checkout.save()

        # Increment promo usage
        promo.usage_count += 1
        promo.save()

        serializer = self.get_serializer(checkout)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete checkout and create order"""
        from commerce.models import PurchaseOrder, PurchaseOrderDetail

        checkout = self.get_object()

        if checkout.is_completed:
            return Response({"error": "Checkout already completed"}, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        order = PurchaseOrder.objects.create(
            buyer=checkout.buyer,
            seller=checkout.buyer,  # Will be updated based on cart items
            warehouse=checkout.shipping_address,
            delivery_term=checkout.delivery_term,
            payment_term=checkout.payment_term,
            payment_mode_id=1,  # Will need to map from checkout.payment_method
            shipping_cost=checkout.shipping_cost,
            currency=checkout.currency,
        )

        # Create order items from cart
        cart_items = checkout.cart.items.filter(is_deleted=False)
        for item in cart_items:
            PurchaseOrderDetail.objects.create(
                order=order,
                product=item.product,
                sku=item.sku,
                no_of_units=item.quantity,
                total_quantity=item.quantity,  # Simplified
                price_per_unit=item.unit_price,
            )

        # Create payment record
        payment = Payment.objects.create(
            order=order,
            payment_method=checkout.payment_method,
            amount=checkout.total_amount,
            currency=checkout.currency,
            status="pending",
        )

        # Mark checkout as completed
        checkout.is_completed = True
        checkout.completed_at = timezone.now()
        checkout.order = order
        checkout.save()

        # Clear cart
        checkout.cart.is_active = False
        checkout.cart.save()

        serializer = self.get_serializer(checkout)
        return Response(serializer.data)


class ProductViewViewSet(viewsets.ModelViewSet):
    queryset = ProductView.objects.all()
    serializer_class = ProductViewSerializer
    filterset_fields = ["product", "viewer"]

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        """Get product view analytics"""
        product_id = request.query_params.get("product_id")
        days = int(request.query_params.get("days", 30))

        from datetime import timedelta

        start_date = timezone.now() - timedelta(days=days)

        query = ProductView.objects.filter(viewed_at__gte=start_date)
        if product_id:
            query = query.filter(product_id=product_id)

        stats = query.aggregate(
            total_views=Count("id"),
            unique_viewers=Count("viewer", distinct=True),
            anonymous_views=Count("id", filter=Q(viewer__isnull=True)),
        )

        return Response(stats)


class SearchQueryViewSet(viewsets.ModelViewSet):
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer
    filterset_fields = ["searcher"]

    @action(detail=False, methods=["get"])
    def popular_searches(self, request):
        """Get most popular search queries"""
        limit = int(request.query_params.get("limit", 10))
        days = int(request.query_params.get("days", 7))

        from datetime import timedelta

        start_date = timezone.now() - timedelta(days=days)

        popular = (
            SearchQuery.objects.filter(searched_at__gte=start_date)
            .values("query")
            .annotate(search_count=Count("id"))
            .order_by("-search_count")[:limit]
        )

        return Response(list(popular))

    @action(detail=False, methods=["get"])
    def trending(self, request):
        """Get trending searches (high growth rate)"""
        limit = int(request.query_params.get("limit", 10))

        from datetime import timedelta

        now = timezone.now()
        last_24h = now - timedelta(days=1)
        prev_24h = now - timedelta(days=2)

        recent = (
            SearchQuery.objects.filter(searched_at__gte=last_24h).values("query").annotate(recent_count=Count("id"))
        )

        previous = (
            SearchQuery.objects.filter(searched_at__gte=prev_24h, searched_at__lt=last_24h)
            .values("query")
            .annotate(prev_count=Count("id"))
        )

        # Calculate growth rate
        trending = []
        for r in recent:
            prev = next((p for p in previous if p["query"] == r["query"]), None)
            prev_count = prev["prev_count"] if prev else 1
            growth = (r["recent_count"] - prev_count) / prev_count * 100
            trending.append({"query": r["query"], "count": r["recent_count"], "growth": growth})

        trending.sort(key=lambda x: x["growth"], reverse=True)
        return Response(trending[:limit])


class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    filterset_fields = ["is_active"]
    lookup_field = "code"

    @action(detail=True, methods=["post"])
    def validate(self, request, code=None):
        """Validate promo code"""
        promo = self.get_object()
        amount = request.data.get("amount")

        if not amount:
            return Response({"error": "amount required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if not promo.is_valid():
            return Response(
                {"valid": False, "error": "Promo code is not valid or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        discount = promo.calculate_discount(amount)
        return Response(
            {
                "valid": True,
                "code": promo.code,
                "discount_amount": discount,
                "final_amount": amount - discount,
            }
        )
