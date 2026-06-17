from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom manager for our email-based User model.

    Django's default UserManager sets username — ours doesn't have one,
    so we override create_user and create_superuser to use email instead.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The email address is required."))

        email = self.normalize_email(email)  # lowercases the domain part
        user = self.model(email=email, **extra_fields)
        user.set_password(password)          # hashes the password — never store plaintext
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Ensure these flags are always True for a superuser
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)