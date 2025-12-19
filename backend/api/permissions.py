from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Allow access only to users with role 'admin' or staff/superuser."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Accept explicit 'admin' role, or Django staff/superuser
        if getattr(user, "role", None) == "admin":
            return True
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            return True
        return False


class IsLandlordRole(permissions.BasePermission):
    """Allow access only to landlords (or staff/superuser)."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) == "landlord":
            return True
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            return True
        return False
