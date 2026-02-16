"""Media serializers for API v2"""

from rest_framework import serializers
from mediaviewer.models.movie import Movie
from mediaviewer.models.tv import TV
from mediaviewer.models.genre import Genre


class GenreSerializer(serializers.ModelSerializer):
    """Serialize Genre model"""

    class Meta:
        model = Genre
        fields = ["id", "genre", "datecreated", "dateedited"]
        read_only_fields = ["id", "datecreated", "dateedited"]


class MovieSerializer(serializers.ModelSerializer):
    """Serialize Movie model"""

    poster_image_url = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "name",
            "date_created",
            "dateedited",
            "poster_image_url",
            "genres",
            "description",
        ]
        read_only_fields = ["id", "date_created", "dateedited"]

    def get_poster_image_url(self, obj):
        """Get poster image URL"""
        try:
            if obj._poster and obj._poster.image:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(obj._poster.image.url)
                return obj._poster.image.url
        except AttributeError:
            pass
        return None

    def get_genres(self, obj):
        """Get genres for the movie"""
        try:
            if obj._poster:
                genres = obj._poster.genre.all()
                return GenreSerializer(genres, many=True).data
        except AttributeError:
            pass
        return []

    @property
    def description(self):
        """Get description from poster"""
        try:
            if hasattr(self, "_poster") and self._poster:
                return self._poster.description
        except AttributeError:
            pass
        return None


class TVSerializer(serializers.ModelSerializer):
    """Serialize TV model"""

    poster_image_url = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()

    class Meta:
        model = TV
        fields = [
            "id",
            "name",
            "date_created",
            "dateedited",
            "poster_image_url",
            "genres",
            "description",
        ]
        read_only_fields = ["id", "date_created", "dateedited"]

    def get_poster_image_url(self, obj):
        """Get poster image URL"""
        try:
            if obj._poster and obj._poster.image:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(obj._poster.image.url)
                return obj._poster.image.url
        except AttributeError:
            pass
        return None

    def get_genres(self, obj):
        """Get genres for the TV show"""
        try:
            if obj._poster:
                genres = obj._poster.genre.all()
                return GenreSerializer(genres, many=True).data
        except AttributeError:
            pass
        return []

    @property
    def description(self):
        """Get description from poster"""
        try:
            if hasattr(self, "_poster") and self._poster:
                return self._poster.description
        except AttributeError:
            pass
        return None
