"""User profile and settings views for API v2"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mediaviewer.models.usersettings import UserSettings
from .serializers import UserSerializer, UserSettingsSerializer


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    GET /api/v2/users/me/ - Get current user profile
    PUT /api/v2/users/me/ - Update current user profile
    """
    if request.method == "GET":
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {
                "error": {
                    "code": "INVALID_DATA",
                    "message": "Invalid profile data",
                    "details": serializer.errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """
    GET /api/v2/users/me/settings/ - Get current user settings
    PUT /api/v2/users/me/settings/ - Update current user settings
    """
    try:
        user_settings = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "SETTINGS_NOT_FOUND",
                    "message": "User settings not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        serializer = UserSettingsSerializer(user_settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        serializer = UserSettingsSerializer(
            user_settings, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {
                "error": {
                    "code": "INVALID_DATA",
                    "message": "Invalid settings data",
                    "details": serializer.errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
