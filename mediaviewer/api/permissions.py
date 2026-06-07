from django.contrib.auth.models import User
from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        if request.user.is_authenticated and request.method in permissions.SAFE_METHODS:
            return True
        return False


class CheckAPIKey(permissions.BasePermission):
    def has_permission(self, request, view):
        if api_key := request.META.get("HTTP_API_KEY"):
            return (
                User.objects.filter(active=True)
                .filter(apikey__key__iexact=api_key.strip())
                .exists()
            )
        return False
