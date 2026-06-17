from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from .models import Order, OrderItem, OrderStatusHistory


def place_order(user) -> Order:
    """
    Creates an order from the user's current cart.

    Flow:
      1. Load the cart with its items (locking product rows to prevent
         a race condition where two requests oversell the same stock).
      2. Validate the cart isn't empty.
      3. Validate stock for EVERY item before creating anything.
      4. Create the Order + OrderItems (snapshotting name/price).
      5. Decrement product stock.
      6. Write the initial OrderStatusHistory entry.
      7. Clear the cart.

    Wrapped in transaction.atomic(): if any step raises, the database
    is rolled back to exactly how it was before this function ran.
    Nothing is left half-done.
    """
    try:
        cart = Cart.objects.select_related().get(user=user)
    except Cart.DoesNotExist:
        raise ValidationError("Your cart is empty.")

    cart_items = list(cart.items.select_related("product").all())

    if not cart_items:
        raise ValidationError("Your cart is empty.")

    with transaction.atomic():
        # select_for_update() locks these product rows until the
        # transaction commits, so a second simultaneous order can't
        # read stale stock numbers and oversell the last unit.
        product_ids = [item.product_id for item in cart_items]
        from products.models import Product
        locked_products = {
            p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        # Validate stock for every item BEFORE creating anything
        for item in cart_items:
            product = locked_products[item.product_id]
            if not product.is_active:
                raise ValidationError(f"'{product.name}' is no longer available.")
            if item.quantity > product.quantity:
                raise ValidationError(
                    f"Only {product.quantity} unit(s) of '{product.name}' available."
                )

        # All validations passed — now create the order
        total_price = sum(item.subtotal for item in cart_items)
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            current_status=Order.Status.PENDING,
        )

        for item in cart_items:
            product = locked_products[item.product_id]
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,   # snapshot
                price=product.price,         # snapshot
                quantity=item.quantity,
            )
            # Deduct stock
            product.quantity -= item.quantity
            product.save(update_fields=["quantity"])

        OrderStatusHistory.objects.create(
            order=order,
            status=Order.Status.PENDING,
            note="Order placed by customer.",
        )

        # Clear the cart now that the order exists
        cart.items.all().delete()

    return order


def update_order_status(order: Order, new_status: str, note: str = "", admin_user=None) -> Order:
    """
    Admin-only operation: transitions an order to a new status and
    writes a corresponding OrderStatusHistory entry. Kept here (not in
    the view) so the same logic can be reused by the admin panel's
    save_model hook or a future management command.
    """
    if new_status not in Order.Status.values:
        raise ValidationError(f"'{new_status}' is not a valid status.")

    order.current_status = new_status
    order.save(update_fields=["current_status"])

    OrderStatusHistory.objects.create(
        order=order,
        status=new_status,
        note=note or f"Status updated to {new_status} by admin.",
    )
    return order