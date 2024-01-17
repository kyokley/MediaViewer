from rest_framework import viewsets

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MediaFileSerializer
from mediaviewer.models import MediaFile


class MediaPathViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = MediaFile.objects.order_by("id")
    serializer_class = MediaFileSerializer
