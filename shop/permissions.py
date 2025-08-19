# shop/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", "user") == "admin"

class IsUserRole(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "role", None) in {"user","admin"}
