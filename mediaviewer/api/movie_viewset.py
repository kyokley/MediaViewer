from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly, IsStaffReadOnlyOrCheckAPIKey
from mediaviewer.api.serializers import MovieSerializer, MCPMovieSerializer
from mediaviewer.models import Movie, Genre


class MovieViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = Movie.objects.order_by("id")
    serializer_class = MovieSerializer

    # TODO: Check this method name and call sig
    def create(self, request):
        if "media_path" not in request.POST:
            raise serializers.ValidationError("'media_path' is a required argument")

        name = request.POST.get("name")
        media_path = request.POST["media_path"]

        movie = Movie.objects.from_path(media_path, name=name)
        serializer = self.serializer_class(movie)
        return Response(serializer.data)


class MCPMovieViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = Movie.objects.filter(hide=False).order_by("id")
    serializer_class = MCPMovieSerializer

    def _filter_by_genre(self, genre):
        if not genre:
            return self.queryset

        if genre_obj := Genre.objects.filter(genre=genre).first():
            movie_set = genre_obj.poster_set.filter(movie__hide=False).values("movie")
            return self.queryset.filter(pk__in=movie_set)
        return self.queryset.none()

    def list(self, request):
        fields = {
            "name": "name__icontains",
            "imdb": "_poster__imdb",
            "tmdb": "_poster__tmdb",
        }

        if "genre" in request.query_params:
            posters = self._filter_by_genre(request.query_params["genre"])
            at_least_one_filter = True
        else:
            posters = self.queryset
            at_least_one_filter = False

        for external_name, internal_name in fields.items():
            if val := request.query_params.get(external_name, None):
                posters = posters.filter(**{internal_name: val})
                at_least_one_filter = True

        if not at_least_one_filter:
            raise serializers.ValidationError(
                f"At least one field of 'genre, {', '.join(fields.keys())}' is required"
            )
        serializer = self.serializer_class(posters, many=True)
        return Response(serializer.data)
