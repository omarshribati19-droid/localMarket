from rest_framework import serializers

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Read-only — order items are snapshots created at order time and
    are never edited directly through the API.
    """
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "price", "quantity", "subtotal")
        read_only_fields = fields

    def get_subtotal(self, obj):
        return str(obj.subtotal)


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ("id", "status", "note", "created_at")
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for GET /api/orders/ — the list view.
    Doesn't include items or full history, just enough for an
    order history screen (id, total, status, date).
    """
    class Meta:
        model = Order
        fields = ("id", "total_price", "current_status", "created_at")
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for GET /api/orders/{id}/ — includes nested items
    and the full status timeline.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "user", "total_price", "current_status",
            "items", "status_history", "created_at", "updated_at",
        )
        read_only_fields = fields


class UpdateOrderStatusSerializer(serializers.Serializer):
    """
    Input serializer for admin PATCH /api/orders/{id}/status/
    """
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")