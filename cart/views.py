from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartItem
from .serializers import CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer
from .services import get_or_create_cart, add_item_to_cart, update_cart_item_quantity


class CartView(generics.RetrieveAPIView):
    """
    GET /api/cart/

    Returns the authenticated user's cart, creating it automatically
    if it doesn't exist yet (lazy creation — see services.py).
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_or_create_cart(self.request.user)


class CartItemCreateView(generics.CreateAPIView):
    """
    POST /api/cart/items/
    Body: {"product_id": 1, "quantity": 2}

    Adds a product to the cart, or increases quantity if already present.
    Returns the FULL updated cart (not just the new item) so the
    frontend can re-render totals immediately without a second request.
    """
    serializer_class = AddCartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.context["product"]   # resolved during validate_product_id
        quantity = serializer.validated_data["quantity"]

        cart = get_or_create_cart(request.user)
        add_item_to_cart(cart, product, quantity)

        return Response(CartSerializer(cart, context={"request": request}).data,
                         status=status.HTTP_201_CREATED)


class CartItemUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/cart/items/{id}/
    Body: {"quantity": 5}

    Updates the quantity of a specific cart item. Scoped to the
    requesting user's own cart only — see get_queryset.
    """
    serializer_class = UpdateCartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # A user can only ever touch their own cart's items, never anyone else's
        return CartItem.objects.filter(cart__user=self.request.user)

    def update(self, request, *args, **kwargs):
        cart_item = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_cart_item_quantity(cart_item, serializer.validated_data["quantity"])

        cart = cart_item.cart
        return Response(CartSerializer(cart, context={"request": request}).data)


class CartItemDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/cart/items/{id}/

    Removes a single item from the cart.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        cart_item = self.get_object()
        cart = cart_item.cart
        cart_item.delete()
        return Response(CartSerializer(cart, context={"request": request}).data,
                         status=status.HTTP_200_OK)


class CartClearView(APIView):
    """
    DELETE /api/cart/

    Removes ALL items from the user's cart in one call.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response(CartSerializer(cart, context={"request": request}).data,
                         status=status.HTTP_200_OK)