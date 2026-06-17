from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that adds created_at and updated_at to any model
    that inherits from it.

    'abstract = True' means Django will NOT create a database table for
    this model itself. It only exists to be inherited. Every child model
    gets the two fields added automatically.

    Usage:
        class Product(TimeStampedModel):
            name = models.CharField(max_length=255)
            # automatically also has created_at and updated_at
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # critical — no table, just a blueprint
        ordering = ["-created_at"]