from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from .serializers import RegisterSerializer, UserSerializer, UpdateProfileSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Public endpoint — anyone can create an account.
    Returns the created user (without password) on success.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Return the public UserSerializer representation, not the
        # RegisterSerializer (which still has password fields defined)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT login serializer to also return the user's
    profile data alongside the access/refresh tokens. This saves the
    frontend an extra request right after login.
    """

    def validate(self, attrs):
        data = super().validate(attrs)  # runs the actual auth check, raises if invalid
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: {"email": "...", "password": "..."}

    Returns: {"access": "...", "refresh": "...", "user": {...}}
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """
    GET   /api/auth/me/  → current user's profile
    PATCH /api/auth/me/  → update first_name, last_name, phone_number

    Requires a valid JWT access token in the Authorization header:
    Authorization: Bearer <access_token>
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)