from django.contrib import admin

from .models import Category, Store, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}  # auto-fills slug as you type the name
    readonly_fields = ("created_at", "updated_at")


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


class ProductImageInline(admin.TabularInline):
    """
    Shows product images directly inside the Product edit page.
    Admin can add/remove images without leaving the product form.
    """
    model = ProductImage
    extra = 1               # show 1 empty row for a new image by default
    readonly_fields = ("created_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "store", "price", "quantity", "is_active", "created_at")
    list_filter = ("is_active", "category", "store")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductImageInline]

    # Group fields logically in the edit form
    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "slug", "category", "store", "description")
        }),
        ("Pricing & Stock", {
            "fields": ("price", "quantity", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),   # hidden by default, click to expand
        }),
    )