"""Authentication views for API v2"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    UserSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/v2/auth/login/
    Login with username and password
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        response_data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    return Response(
        {
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid username or password",
                "details": serializer.errors,
            }
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_passkey(request):
    """
    POST /api/v2/auth/login-passkey/
    Login with passkey/WebAuthn

    TODO: Implement passkey authentication
    """
    return Response(
        {
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Passkey authentication not yet implemented",
            }
        },
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    POST /api/v2/auth/refresh/
    Refresh JWT access token
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if serializer.is_valid():
        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            new_access = refresh.access_token

            response_data = {
                "access": str(new_access),
                "refresh": str(refresh),
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response(
                {
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid refresh token",
                        "details": str(e),
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

    return Response(
        {
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Refresh token is required",
                "details": serializer.errors,
            }
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/v2/auth/logout/
    Logout user (invalidate refresh token)

    TODO: Implement token blacklisting
    """
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    GET /api/v2/auth/me/
    Get current authenticated user
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)
