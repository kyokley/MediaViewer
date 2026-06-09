from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffReadOnlyOrCheckAPIKey
from mediaviewer.api.serializers import TVSerializer
from mediaviewer.models import TV


class TVViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = TV.objects.order_by("id")
    serializer_class = TVSerializer

    def create(self, request):
        if "media_path" not in request.POST:
            raise serializers.ValidationError("'media_path' is a required argument")

        name = request.POST.get("name")
        media_path = request.POST["media_path"]

        tv = TV.objects.from_path(media_path, name=name)
        serializer = self.serializer_class(tv)
        return Response(serializer.data)


class TVByIMDBViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = TV.objects.filter(hide=False)
    serializer_class = TVSerializer

    def list(self, request):
        if "imdb_id" not in request.query_params:
            raise serializers.ValidationError("'imdb_id' is a required argument")
        imdb_id = request.query_params["imdb_id"]
        tvs = self.queryset.filter(imdb_id=imdb_id).filter(hide=False)
        serializer = self.serializer_class(tvs, many=True)
        return Response(serializer.data)


class TVByGenreViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = TV.objects.filter(hide=False)
    serializer_class = TVSerializer

    def list(self, request):
        if "genre" not in request.query_params:
            raise serializers.ValidationError("'genre' is a required argument")
        genre = request.query_params["genre"]
        tvs = self.queryset.filter(_poster__genre__genre=genre).filter(hide=False)
        serializer = self.serializer_class(tvs, many=True)
        return Response(serializer.data)
