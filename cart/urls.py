from django.urls import path

from .views import (
    CartView,
    CartItemCreateView,
    CartItemUpdateView,
    CartItemDeleteView,
    CartClearView,
)

urlpatterns = [
    path("", CartView.as_view(), name="cart-detail"),
    path("clear/", CartClearView.as_view(), name="cart-clear"),
    path("items/", CartItemCreateView.as_view(), name="cart-item-create"),
    path("items/<int:pk>/", CartItemUpdateView.as_view(), name="cart-item-update"),
    path("items/<int:pk>/delete/", CartItemDeleteView.as_view(), name="cart-item-delete"),
]