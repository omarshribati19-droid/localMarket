from django.db import models
from django.conf import settings

from core.models import TimeStampedModel
from products.models import Product


class Cart(TimeStampedModel):
    """
    One cart per user. Created automatically when a user first adds an item.

    We use settings.AUTH_USER_MODEL (not a direct import of User) to avoid
    circular import issues. Django resolves it correctly at runtime.

    OneToOneField means each user can only ever have one cart row.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,          # user deleted → cart deleted
        related_name="cart",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cart of {self.user.email}"

    @property
    def total_price(self):
        """
        Compute cart total in Python, not SQL.
        Called by the serializer — never trust the client to send a total.
        """
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(TimeStampedModel):
    """
    A single product line inside a cart.

    unique_together ensures a product can only appear once per cart
    (instead of two rows for the same product — we just update quantity).
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,          # cart cleared → all items gone
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,          # product deleted → remove from carts
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        # Enforced at the database level: one row per product per cart
        unique_together = ("cart", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart}"

    @property
    def subtotal(self):
        """Price × quantity for this line item."""
        return self.product.price * self.quantity