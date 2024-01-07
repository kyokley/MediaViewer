from rest_framework import viewsets
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
        name = request.POST['name']
        path = request.POST['path']

        movie = Movie.objects.from_filename(name, path)
        serializer = self.serializer_class(movie)
        return Response(serializer.data)
