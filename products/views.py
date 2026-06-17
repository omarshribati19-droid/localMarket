from rest_framework import viewsets

from core.permissions import IsAdminOrReadOnly
from .models import Category, Store, Product
from .serializers import (
    CategorySerializer,
    StoreSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
)
from .filters import ProductFilter


class CategoryViewSet(viewsets.ModelViewSet):
    """
    /api/categories/         GET (list, public), POST (admin)
    /api/categories/{slug}/  GET (detail, public), PUT/PATCH/DELETE (admin)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    search_fields = ["name"]


class StoreViewSet(viewsets.ModelViewSet):
    """
    /api/stores/        GET (list, public), POST (admin)
    /api/stores/{id}/   GET (detail, public), PUT/PATCH/DELETE (admin)
    """
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    """
    /api/products/         GET (list, public, filterable/searchable)
                            POST (admin)
    /api/products/{slug}/  GET (detail, public)
                            PUT/PATCH/DELETE (admin)

    Query params supported:
      ?search=wallet              — searches name & description
      ?category=wallets           — filter by category slug
      ?min_price=10&max_price=50  — price range
      ?ordering=price / -price / created_at / -created_at
    """
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]

    def get_queryset(self):
        """
        Non-admin users only ever see active products.
        Admins (is_staff) see everything, including inactive/hidden ones,
        so they can manage the full catalogue.
        """
        qs = Product.objects.select_related("category", "store").prefetch_related("images")
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductWriteSerializer  # create, update, partial_update