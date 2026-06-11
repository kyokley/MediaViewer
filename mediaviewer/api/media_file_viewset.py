from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import serializers

from rest_framework.response import Response
from mediaviewer.models import MediaFile
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.api.permissions import IsStaffReadOnlyOrCheckAPIKey
from mediaviewer.api.serializers import MediaFileSerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = MediaFile.objects.order_by("id")
    serializer_class = MediaFileSerializer


class MediaFileAutoplayViewSet(viewsets.ViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)

    def retrieve(self, request, pk=None):
        user = request.user
        mf = get_object_or_404(MediaFile, pk=pk)
        dt = DownloadToken.objects.from_media_file(user, mf)

        downloadlink = mf.autoplayDownloadLink(dt.guid)
        return Response({"link": downloadlink})


class MCPMediaFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = MediaFile.objects.filter(hide=False)
    serializer_class = MediaFileSerializer

    def list(self, request):
        if "tv_id" not in request.query_params:
            raise serializers.ValidationError("'tv_id' is a required argument")

        tv_id = request.query_params["tv_id"]
        mfs = self.queryset.filter(media_path__tv=tv_id)
        serializer = self.serializer_class(mfs, many=True)
        return Response(serializer.data)
