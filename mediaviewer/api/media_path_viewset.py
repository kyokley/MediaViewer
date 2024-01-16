from rest_framework import viewsets, serializers
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MediaPathSerializer
from mediaviewer.models import MediaPath, TV


class MediaPathViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = MediaPath.objects.order_by("id")
    serializer_class = MediaPathSerializer

    def create(self, request):
        if 'path' not in request.POST:
            raise serializers.ValidationError(
                "'path' is a required argument"
            )

        path = request.POST['path']

        mp = MediaPath.objects.filter(_path=path).first()

        if not mp:
            TV.objects.from_path(path)
            mp = MediaPath.objects.get(_path=path)

        serializer = self.serializer_class(mp)
        return Response(serializer.data)
