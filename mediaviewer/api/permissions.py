from django.contrib.auth.models import User
from django.contrib.auth import login
from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        if request.user.is_authenticated and request.method in permissions.SAFE_METHODS:
            return True
        return False


class IsStaffReadOnlyOrCheckAPIKey(IsStaffOrReadOnly):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS and (
            api_key := request.META.get("HTTP_API_KEY")
        ):
            if user := (
                User.objects.filter(apikey__key__iexact=api_key.strip()).first()
            ):
                if user.is_active:
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )
                    return True
        return super().has_permission(request, view)
