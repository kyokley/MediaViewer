from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from django.http import JsonResponse
from mediaviewer.models import MediaFile
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.api.permissions import IsStaffOrReadOnly
from mediaviewer.api.serializers import MediaFileSerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = MediaFile.objects.order_by("id")
    serializer_class = MediaFileSerializer


class MediaFileAutoplayViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        user = request.user
        mf = get_object_or_404(MediaFile, pk=pk)
        dt = DownloadToken.objects.from_media_file(user, mf)

        downloadlink = mf.autoplayDownloadLink(dt.guid)
        return JsonResponse({"link": downloadlink})
