from rest_framework import viewsets
from rest_framework.response import Response

from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import TVSerializer
from mediaviewer.models import TV


class TVViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = TV.objects.order_by("id")
    serializer_class = TVSerializer

    # TODO: Check this method name and call sig
    def create(self, request):
        name = request.POST['name']
        path = request.POST['path']

        tv = TV.objects.from_filename(name, path)
        serializer = self.serializer_class(tv)
        return Response(serializer.data)
