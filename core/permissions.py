from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Anyone (including anonymous users) can read (GET, HEAD, OPTIONS).
    Only staff/admin users can write (POST, PUT, PATCH, DELETE).

    Used on: Category, Store, Product viewsets.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: only the owner of the object (e.g. the
    customer who placed the order) or an admin/staff user can access it.

    Assumes the object has a `.user` attribute (Order does).
    Used on: Order detail/list views.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return obj.user_id == request.user.id