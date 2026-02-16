"""Additional serializers for API v2 (requests, video progress, comments)"""

from rest_framework import serializers
from mediaviewer.models.request import Request
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.comment import Comment


class RequestSerializer(serializers.ModelSerializer):
    """Serialize media request model"""

    user_username = serializers.CharField(source="user.username", read_only=True)
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = [
            "id",
            "name",
            "done",
            "user_username",
            "vote_count",
            "datecreated",
            "dateedited",
        ]
        read_only_fields = ["id", "datecreated", "dateedited", "vote_count"]

    def get_vote_count(self, obj):
        """Get the number of votes for this request"""
        try:
            return obj.numberOfVotes()
        except Exception:
            return 0


class VideoProgressSerializer(serializers.ModelSerializer):
    """Serialize video progress model"""

    movie_name = serializers.CharField(
        source="movie.name", read_only=True, allow_null=True
    )
    media_file_name = serializers.CharField(
        source="media_file.filename", read_only=True, allow_null=True
    )

    class Meta:
        model = VideoProgress
        fields = [
            "id",
            "hashed_filename",
            "offset",
            "date_edited",
            "movie_name",
            "media_file_name",
        ]
        read_only_fields = ["id", "date_edited"]


class CommentSerializer(serializers.ModelSerializer):
    """Serialize comment model"""

    user_username = serializers.CharField(source="user.username", read_only=True)
    movie_name = serializers.CharField(
        source="movie.name", read_only=True, allow_null=True
    )
    media_file_name = serializers.CharField(
        source="media_file.filename", read_only=True, allow_null=True
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "user_username",
            "movie_name",
            "media_file_name",
            "viewed",
            "date_created",
            "date_modified",
        ]
        read_only_fields = ["id", "user_username", "date_created", "date_modified"]
