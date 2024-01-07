from rest_framework import viewsets

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MediaPathSerializer
from mediaviewer.models import MediaPath


class MediaPathViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = MediaPath.objects.order_by("id")
    serializer_class = MediaPathSerializer
