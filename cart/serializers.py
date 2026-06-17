from rest_framework import serializers

from products.models import Product
from .models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    """
    Minimal product info shown inside a cart item — just enough for the
    frontend to render a cart row (thumbnail, name, price) without a
    second request to /api/products/{slug}/.
    """

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "price", "quantity", "is_active", "primary_image")

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image:
            request = self.context.get("request")
            url = image.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """
    Read representation of a cart line item, including the nested
    product snapshot and a computed subtotal (price × quantity).
    """

    product = CartProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal", "created_at")

    def get_subtotal(self, obj):
        return str(obj.subtotal)  # str() avoids float rounding issues in JSON


class CartSerializer(serializers.ModelSerializer):
    """
    Full cart representation: nested items + computed total_price and
    total_items. This is the response shape for GET /api/cart/.
    """

    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "items", "total_items", "total_price", "created_at", "updated_at")

    def get_total_price(self, obj):
        return str(obj.total_price)

    def get_total_items(self, obj):
        return obj.total_items


class AddCartItemSerializer(serializers.Serializer):
    """
    Input serializer for POST /api/cart/items/
    Not a ModelSerializer — this is a plain input contract, since the
    actual cart-item creation/update logic (with stock checks) lives
    in the view, not here.
    """

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or unavailable.")
        self.context["product"] = product  # pass the resolved object forward to the view
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Input serializer for PATCH /api/cart/items/{id}/
    """
    quantity = serializers.IntegerField(min_value=1)