from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Custom user model for localMarket.

    We extend AbstractUser so we keep Django's built-in auth machinery
    (password hashing, permissions, groups) while adding our own fields
    and switching the login identifier from username to email.
    """

    # Remove the username field entirely — we don't want it
    username = None

    # Make email the unique login identifier
    email = models.EmailField(_("email address"), unique=True)

    phone_number = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tell Django: "email is the login field, not username"
    USERNAME_FIELD = "email"

    # Fields prompted when running createsuperuser (email is already included)
    REQUIRED_FIELDS = ["first_name", "last_name"]

    # Our custom manager handles create_user / create_superuser correctly
    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()