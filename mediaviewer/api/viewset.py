from django.shortcuts import get_object_or_404
from rest_framework import permissions, views, viewsets
from rest_framework.response import Response as RESTResponse

from mediaviewer.api.serializers import (CommentSerializer,
                                         DownloadTokenSerializer,
                                         FilenameScrapeFormatSerializer,
                                         MessageSerializer)
from mediaviewer.log import log
from mediaviewer.models import (Comment, DownloadToken, FilenameScrapeFormat,
                                MediaFile, Message)


class DownloadTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DownloadTokenSerializer

    def retrieve(self, request, pk=None):
        log.debug(f"Attempting to find token with guid = {pk}")
        queryset = DownloadToken.objects.filter(guid=pk)
        obj = get_object_or_404(queryset, guid=pk)
        if obj:
            log.debug(f"Found token. isValid: {obj.isvalid}")
        serializer = self.serializer_class(obj)
        return RESTResponse(serializer.data)


class FilenameScrapeFormatViewSet(viewsets.ModelViewSet):
    queryset = FilenameScrapeFormat.objects.all()
    serializer_class = FilenameScrapeFormatSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


class InferScrapersView(views.APIView):
    def get(self, request, *args, **kwargs):
        filename = request.GET["title"]
        tv = FilenameScrapeFormat.tv_for_filename(filename)
        return RESTResponse({"path": str(tv.media_path.path) if tv else ""})

    def post(self, request, *args, **kwargs):
        try:
            MediaFile.objects.infer_missing_scrapers()
            return RESTResponse({"success": True})
        except Exception as e:
            return RESTResponse({"success": False, "error": str(e)})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.none()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(user=user)
        log.debug("Returning Comment objects")
        return queryset
