from rest_framework import viewsets

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import TVSerializer
from mediaviewer.models import TV


class TVViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = TV.objects.order_by("id")
    serializer_class = TVSerializer
