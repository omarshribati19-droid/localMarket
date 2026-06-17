from django.db import models
from django.conf import settings

from core.models import TimeStampedModel
from products.models import Product


class Order(TimeStampedModel):
    """
    A placed order from a customer.

    Key design decisions:
    - current_status uses TextChoices so the valid values are enforced
      at the Python and database level — no free-form strings
    - total_price is stored (not computed) because product prices can
      change after the order is placed — we snapshot it at order time
    - user FK is SET_NULL so that if a user account is deleted, we
      keep the order history for business records
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,         # keep order even if user is deleted
        null=True,
        related_name="orders",
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} by {self.user.email if self.user else 'deleted user'}"


class OrderItem(TimeStampedModel):
    """
    A snapshot of one product line at the time the order was placed.

    Critical: we store product_name and price AS THEY WERE at order time.
    If the product is renamed or repriced later, this order record stays
    accurate. The FK to Product is SET_NULL so we keep the record even
    if the product is later deleted from the catalogue.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,         # product deleted → item stays with null FK
        null=True,
        related_name="order_items",
    )

    # Snapshot fields — written once at order creation, never updated
    product_name = models.CharField(max_length=255)   # snapshot of product.name
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot of product.price
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        # Auto-fill the snapshot fields from the linked product
        # This runs at creation time only (product is still set)
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} (Order #{self.order.id})"

    @property
    def subtotal(self):
        return self.price * self.quantity


class OrderStatusHistory(TimeStampedModel):
    """
    Append-only log of every status change on an order.

    Whenever an admin updates an order's status, we write a new row here.
    This gives customers a full timeline: "Pending → Confirmed → Shipped".
    We never delete or update rows in this table.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
    )
    note = models.TextField(blank=True)    # optional admin note, e.g. "Dispatched via DHL"

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"

    def __str__(self):
        return f"Order #{self.order.id} → {self.status} at {self.created_at:%Y-%m-%d %H:%M}"