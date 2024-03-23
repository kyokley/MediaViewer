from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MovieSerializer
from mediaviewer.models import Movie


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
