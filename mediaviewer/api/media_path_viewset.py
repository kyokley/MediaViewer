from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MediaPathSerializer
from mediaviewer.models import TV, MediaPath, Movie


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

        mp = MediaPath.objects.filter(_path=path).first()

        if not mp:
            media_class.objects.from_path(path, tv_id=tv_id, movie_id=movie_id)
            mp = MediaPath.objects.get(_path=path)

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
