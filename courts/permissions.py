from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user

class AllowAnyCreateIsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Allow unauthenticated users to create bookings,
    but require authentication for other operations.
    """
    def has_permission(self, request, view):
        # Allow unauthenticated users to create bookings
        if request.method == 'POST':
            return True
            
        # For all other operations, require authentication
        return bool(
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_authenticated
        )