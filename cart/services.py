from rest_framework.exceptions import ValidationError

from products.models import Product
from .models import Cart, CartItem


def get_or_create_cart(user) -> Cart:
    """
    Every authenticated user has exactly one cart. We create it lazily
    on first use rather than at registration time — most users never
    need a cart, so why create one for everybody up front.
    """
    cart, _created = Cart.objects.get_or_create(user=user)
    return cart


def add_item_to_cart(cart: Cart, product: Product, quantity: int) -> CartItem:
    """
    Adds a product to the cart, or increments quantity if it's already
    in the cart (since CartItem has unique_together = (cart, product)).

    Stock validation happens here, not in the serializer, because it
    needs to check against the EXISTING quantity already in the cart
    (someone adding 3 more of an item that already has 2 in cart, with
    only 4 in stock, should fail — the serializer alone can't know that).
    """
    existing_item = CartItem.objects.filter(cart=cart, product=product).first()
    requested_total = quantity + (existing_item.quantity if existing_item else 0)

    if requested_total > product.quantity:
        raise ValidationError(
            f"Only {product.quantity} unit(s) of '{product.name}' available. "
            f"You already have {existing_item.quantity if existing_item else 0} in your cart."
        )

    if existing_item:
        existing_item.quantity = requested_total
        existing_item.save()
        return existing_item

    return CartItem.objects.create(cart=cart, product=product, quantity=quantity)


def update_cart_item_quantity(cart_item: CartItem, quantity: int) -> CartItem:
    """
    Updates the quantity of an existing cart item, re-validating stock
    against the CURRENT product quantity (stock may have changed since
    the item was first added).
    """
    if quantity > cart_item.product.quantity:
        raise ValidationError(
            f"Only {cart_item.product.quantity} unit(s) of '{cart_item.product.name}' available."
        )
    cart_item.quantity = quantity
    cart_item.save()
    return cart_item