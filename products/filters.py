import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Enables query params like:
      /api/products/?category=wallets
      /api/products/?store=2
      /api/products/?min_price=10&max_price=100
    """

    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    store = django_filters.NumberFilter(field_name="store__id")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["category", "store", "min_price", "max_price"]