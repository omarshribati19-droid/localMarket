from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel


class Category(TimeStampedModel):
    """
    Product categories (e.g. Wallets, Bags, Accessories).

    We use a slug for clean URLs: /products/?category=wallets
    instead of /products/?category=1
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Store(TimeStampedModel):
    """
    Represents a physical or local store whose products we sell.

    For the MVP, the admin team manually adds stores and assigns
    products to them. Store owners have no accounts or access.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    """
    A product listed for sale on the platform.

    Key design decisions:
    - category: PROTECT prevents deleting a category that has products
    - store: PROTECT prevents deleting a store that has products
    - slug: used for clean URLs instead of numeric IDs
    - is_active: admins hide products without deleting them
    - quantity: tracks available stock
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,          # can't delete a category that has products
        related_name="products",
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,          # can't delete a store that has products
        related_name="products",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        """Convenience property used in serializers and templates."""
        return self.quantity > 0


class ProductImage(TimeStampedModel):
    """
    One or more images attached to a product.

    We separate this into its own model (instead of a single ImageField
    on Product) so that each product can have multiple images.
    The admin team uploads images manually via Django Admin.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,          # delete product → delete its images too
        related_name="images",
    )
    image = models.ImageField(upload_to="products/images/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"