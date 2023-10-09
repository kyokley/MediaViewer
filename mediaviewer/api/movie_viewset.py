from rest_framework import viewsets
from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.models import Movie
from mediaviewer.api.serializers import MovieSerializer


class MovieViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = Movie.objects.order_by('id')
    serializer_class = MovieSerializer
