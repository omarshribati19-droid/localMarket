from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a user. Used for /me/ and nested in
    other responses (e.g. inside Order). Never exposes the password.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "is_staff",
            "created_at",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new customer signup.

    - password is write_only: it's accepted in the request but never
      returned in any response.
    - password_confirm is a non-model field used only for validation.
    - validate_password() runs Django's built-in password strength rules
      (min length, not too common, not entirely numeric, etc).
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        # Remove password_confirm — it's not a real model field
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        # Use our custom manager's create_user so the password is hashed
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Used for PATCH /api/auth/me/ — customers can update their own
    name and phone number, but not email or staff status here.
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number")