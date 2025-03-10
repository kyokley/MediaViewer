from rest_framework import viewsets

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import CollectionSerializer
from mediaviewer.models import Collection


class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = Collection.objects.order_by("id")
    serializer_class = CollectionSerializer
