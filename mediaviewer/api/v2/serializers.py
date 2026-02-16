"""Serializers for API v2"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from mediaviewer.models.usersettings import UserSettings


class UserSerializer(serializers.ModelSerializer):
    """Serialize User model"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "avatar_url",
        ]
        read_only_fields = ["id", "is_staff"]

    def get_avatar_url(self, obj):
        """Get avatar URL for user"""
        # TODO: Implement avatar URL logic when avatars are supported
        return None


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serialize UserSettings model"""

    class Meta:
        model = UserSettings
        fields = [
            "id",
            "dark_theme",
            "items_per_page",
            "autoplay_next",
            "default_quality",
            "subtitle_language",
            "volume_level",
            "email_notifications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    # Map existing fields to API v2 naming convention
    def to_representation(self, instance):
        """Convert model fields to API response"""
        data = super().to_representation(instance)
        # Map existing UserSettings fields
        data = {
            "id": instance.id,
            "dark_theme": instance.theme == UserSettings.DARK,
            "items_per_page": 50,  # Default, could be configurable
            "autoplay_next": instance.binge_mode,
            "default_quality": "auto",  # Default quality
            "subtitle_language": "en",  # Default language
            "volume_level": 1.0,  # Default volume
            "email_notifications": True,  # Default, could be configurable
            "created_at": instance.datecreated.isoformat()
            if instance.datecreated
            else None,
            "updated_at": instance.dateedited.isoformat()
            if instance.dateedited
            else None,
        }
        return data

    def update(self, instance, validated_data):
        """Update UserSettings from API data"""
        # Map API fields back to model fields
        if "dark_theme" in validated_data:
            instance.theme = (
                UserSettings.DARK
                if validated_data.get("dark_theme")
                else UserSettings.LIGHT
            )
        if "autoplay_next" in validated_data:
            instance.binge_mode = validated_data.get("autoplay_next")

        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """Serialize login request"""

    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=128, write_only=True, required=True)

    def validate(self, data):
        """Validate username and password"""
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        data["user"] = user
        return data


class LoginResponseSerializer(serializers.Serializer):
    """Serialize login response"""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class RefreshTokenSerializer(serializers.Serializer):
    """Serialize refresh token request"""

    refresh = serializers.CharField(required=True)


class RefreshTokenResponseSerializer(serializers.Serializer):
    """Serialize refresh token response"""

    access = serializers.CharField()
    refresh = serializers.CharField(required=False)
