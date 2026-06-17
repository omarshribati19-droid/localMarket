from rest_framework import serializers

from .models import Category, Store, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "created_at")
        read_only_fields = ("id", "slug", "created_at")


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ("id", "name", "description", "phone_number", "is_active", "created_at")
        read_only_fields = ("id", "created_at")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "is_primary")


class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the LIST endpoint (/api/products/).
    We don't include all images here — just enough to render a product
    card in a grid: name, price, one thumbnail, category name.
    Keeping list responses small matters for performance at scale.
    """

    category = serializers.StringRelatedField()      # shows category name, not full object
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "price", "quantity",
            "is_active", "category", "primary_image",
        )

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image:
            request = self.context.get("request")
            url = image.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for the DETAIL endpoint (/api/products/{slug}/).
    Includes nested category, store, and all images — everything the
    frontend needs to render a full product page in one request.
    """

    category = CategorySerializer(read_only=True)
    store = StoreSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "price", "quantity",
            "is_active", "is_in_stock", "category", "store", "images",
            "created_at",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    """
    Used for admin create/update (POST, PATCH, PUT).
    Accepts category_id and store_id as plain IDs rather than nested
    objects — that's how you write a FK, vs. how you read one.
    """

    class Meta:
        model = Product
        fields = (
            "id", "name", "category", "store", "description",
            "price", "quantity", "is_active",
        )