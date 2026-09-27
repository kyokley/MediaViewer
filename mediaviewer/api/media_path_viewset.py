import json

from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MediaPathSerializer
from mediaviewer.models import TV, MediaPath, Movie
from mediaviewer.models.mediapath import B2_URI_PREFIX


class _MediaPathViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = MediaPath.objects.none()
    serializer_class = MediaPathSerializer

    def _create(self, media_class, request):
        if "path" not in request.POST:
            raise serializers.ValidationError("'path' is a required argument")

        path = request.POST["path"]
        tv_id = request.POST.get("tv")
        movie_id = request.POST.get("movie")
        filename = request.POST.get("filename")
        subtitle_files = request.POST.get("subtitle_files")
        if subtitle_files:
            try:
                subtitle_files = json.loads(subtitle_files)
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    "subtitle_files must be a valid JSON list"
                )

        if path.startswith(B2_URI_PREFIX):
            bucket, _, key = path[len(B2_URI_PREFIX) :].partition("/")
            if not bucket:
                raise serializers.ValidationError("B2 path must include a bucket name")
            if not key:
                raise serializers.ValidationError("B2 path must include a key")

        mp = MediaPath.objects.filter(_path=path).first()

        if not mp:
            media_class.objects.from_path(path, tv_id=tv_id, movie_id=movie_id)
            mp = MediaPath.objects.get(_path=path)

        if filename and mp.filename != filename:
            mp.filename = filename
            mp.save()

        if subtitle_files and mp.subtitle_files != subtitle_files:
            mp.subtitle_files = subtitle_files
            mp.save()

        serializer = self.serializer_class(mp)
        return Response(serializer.data)


class TVMediaPathViewSet(_MediaPathViewSet):
    queryset = MediaPath.objects.filter(tv__isnull=False).order_by("id")

    def create(self, request):
        return self._create(TV, request)


class MovieMediaPathViewSet(_MediaPathViewSet):
    queryset = MediaPath.objects.filter(movie__isnull=False).order_by("id")

    def create(self, request):
        return self._create(Movie, request)
