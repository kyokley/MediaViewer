from rest_framework import serializers, viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import TVSerializer
from mediaviewer.models import TV


class TVViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = TV.objects.order_by("id")
    serializer_class = TVSerializer

    def create(self, request):
        if "media_path" not in request.POST:
            raise serializers.ValidationError("'media_path' is a required argument")

        name = request.POST.get("name")
        media_path = request.POST["media_path"]

        tv = TV.objects.from_path(media_path, name=name)
        serializer = self.serializer_class(tv)
        return Response(serializer.data)
