from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffReadOnlyOrCheckAPIKey
from mediaviewer.api.serializers import TVSerializer
from mediaviewer.models import TV, Genre


class TVViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = TV.objects.filter(hide=False).order_by("id")
    serializer_class = TVSerializer

    def create(self, request):
        if "media_path" not in request.POST:
            raise serializers.ValidationError("'media_path' is a required argument")

        name = request.POST.get("name")
        media_path = request.POST["media_path"]

        tv = TV.objects.from_path(media_path, name=name)
        serializer = self.serializer_class(tv)
        return Response(serializer.data)

    def list(self, request):
        fields = {
            "name": "name__icontains",
            "imdb": "_poster__imdb",
            "tmdb": "_poster__tmdb",
        }

        posters = self.queryset
        at_least_one_filter = False
        for external_name, internal_name in fields.items():
            if val := request.query_params.get(external_name, None):
                posters = posters.filter(**{internal_name: val})
                at_least_one_filter = True

        if not at_least_one_filter:
            raise serializers.ValidationError(
                f"At least one field of '{', '.join(fields.keys())}' is required"
            )
        serializer = self.serializer_class(posters, many=True)
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
        if genre_obj := Genre.objects.filter(genre=genre).first():
            tv_set = genre_obj.poster_set.filter(tv__hide=False).values("tv")
            tvs = self.queryset.filter(pk__in=tv_set)
            serializer = self.serializer_class(tvs, many=True)
            return Response(serializer.data)
        raise serializers.ValidationError("Genre not found")
