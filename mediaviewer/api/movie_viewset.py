from rest_framework import viewsets

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MovieSerializer
from mediaviewer.models import Movie


class MovieViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = Movie.objects.order_by("id")
    serializer_class = MovieSerializer
