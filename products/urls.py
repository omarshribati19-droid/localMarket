from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, StoreViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("stores", StoreViewSet, basename="store")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls