from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwnerOrAdmin
from .models import Order
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    UpdateOrderStatusSerializer,
)
from .services import place_order, update_order_status


class OrderCreateView(APIView):
    """
    POST /api/orders/

    Places an order from the authenticated user's current cart.
    No request body needed — everything comes from the cart server-side.
    This is intentional: the client never gets to dictate prices or
    quantities at order time, preventing tampering.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order = place_order(request.user)
        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(generics.ListAPIView):
    """
    GET /api/orders/

    Customers see only their own orders. Admins (is_staff) see every
    order on the platform — same endpoint, scoped queryset.
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)


class OrderDetailView(generics.RetrieveAPIView):
    """
    GET /api/orders/{id}/

    Returns full order details including items and status history.
    IsOwnerOrAdmin ensures a customer can't view someone else's order
    by guessing an ID.
    """
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]


class OrderStatusUpdateView(APIView):
    """
    PATCH /api/orders/{id}/status/
    Body: {"status": "shipped", "note": "Dispatched via local courier"}

    Admin-only. Updates the order's status and appends a history entry.
    """
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = update_order_status(
            order,
            new_status=serializer.validated_data["status"],
            note=serializer.validated_data.get("note", ""),
            admin_user=request.user,
        )
        return Response(OrderDetailSerializer(order).data)