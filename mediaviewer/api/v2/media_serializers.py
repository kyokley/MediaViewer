"""Media serializers for API v2"""

from rest_framework import serializers
from mediaviewer.models.movie import Movie
from mediaviewer.models.tv import TV
from mediaviewer.models.genre import Genre
from mediaviewer.models.mediafile import MediaFile


class GenreSerializer(serializers.ModelSerializer):
    """Serialize Genre model"""

    name = serializers.CharField(source="genre")

    class Meta:
        model = Genre
        fields = ["id", "name", "datecreated", "dateedited"]
        read_only_fields = ["id", "datecreated", "dateedited"]


class MovieSerializer(serializers.ModelSerializer):
    """Serialize Movie model"""

    poster_image_url = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "name",
            "date_created",
            "date_edited",
            "poster_image_url",
            "genres",
            "description",
        ]
        read_only_fields = ["id", "date_created", "date_edited"]

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

    def get_description(self, obj):
        """Get description from poster"""
        try:
            if obj._poster:
                return obj._poster.plot or obj._poster.extendedplot
        except AttributeError:
            pass
        return None


class TVSerializer(serializers.ModelSerializer):
    """Serialize TV model"""

    poster_image_url = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = TV
        fields = [
            "id",
            "name",
            "date_created",
            "date_edited",
            "poster_image_url",
            "genres",
            "description",
        ]
        read_only_fields = ["id", "date_created", "date_edited"]

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

    def get_description(self, obj):
        """Get description from poster"""
        try:
            if obj._poster:
                return obj._poster.plot or obj._poster.extendedplot
        except AttributeError:
            pass
        return None


class EpisodeSerializer(serializers.ModelSerializer):
    """Serialize MediaFile (episode) model"""

    episode_name = serializers.SerializerMethodField()
    watched = serializers.SerializerMethodField()
    plot = serializers.SerializerMethodField()
    overview = serializers.SerializerMethodField()
    air_date = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    file_size = serializers.IntegerField(source="size", read_only=True)

    class Meta:
        model = MediaFile
        fields = [
            "id",
            "season",
            "episode",
            "display_name",
            "episode_name",
            "date_created",
            "watched",
            "plot",
            "overview",
            "air_date",
            "thumbnail_url",
            "file_size",
        ]
        read_only_fields = ["id", "date_created"]

    def get_episode_name(self, obj):
        """Get episode name from poster"""
        try:
            if obj._poster and obj._poster.episodename:
                return obj._poster.episodename
        except AttributeError:
            pass
        return None

    def get_watched(self, obj):
        """Check if episode has been watched by current user"""
        request = self.context.get("request")
        if request and request.user:
            return obj.comments.filter(user=request.user, viewed=True).exists()
        return False

    def get_plot(self, obj):
        """Get episode plot/summary"""
        try:
            if obj._poster:
                return obj._poster.plot or obj._poster.extendedplot
        except AttributeError:
            pass
        return None

    def get_overview(self, obj):
        """Get episode extended plot/overview"""
        try:
            if obj._poster and obj._poster.extendedplot:
                return obj._poster.extendedplot
        except AttributeError:
            pass
        return None

    def get_air_date(self, obj):
        """Get episode air date"""
        try:
            if obj._poster and obj._poster.release_date:
                return obj._poster.release_date.isoformat()
        except AttributeError:
            pass
        return None

    def get_thumbnail_url(self, obj):
        """Get episode thumbnail URL"""
        try:
            if obj._poster and obj._poster.image:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(obj._poster.image.url)
                return obj._poster.image.url
        except AttributeError:
            pass
        return None
