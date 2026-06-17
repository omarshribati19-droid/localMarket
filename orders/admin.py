from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # These fields are snapshots — never editable after the order is placed
    readonly_fields = ("product", "product_name", "price", "quantity", "subtotal", "created_at")

    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = "Subtotal"


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "note", "created_at")  # history is append-only, never edit


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "current_status", "created_at")
    list_filter = ("current_status",)
    search_fields = ("user__email", "id")
    readonly_fields = ("total_price", "user", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    fieldsets = (
        ("Order Info", {
            "fields": ("user", "total_price", "current_status")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        When an admin changes the status dropdown and saves, we delegate
        to the SAME service function the API uses (orders.services.
        update_order_status). This guarantees Django Admin and the API
        can never get out of sync on how a status change is recorded.
        """
        if change:
            original = Order.objects.get(pk=obj.pk)
            if original.current_status != obj.current_status:
                from .services import update_order_status
                update_order_status(
                    original,
                    new_status=obj.current_status,
                    note=f"Status updated via admin by {request.user.email}",
                    admin_user=request.user,
                )
                return  # update_order_status already saved the order
        super().save_model(request, obj, form, change)