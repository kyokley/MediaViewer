from django.shortcuts import get_object_or_404
from rest_framework import viewsets, views
from rest_framework.response import Response as RESTResponse
from rest_framework import permissions, authentication
from mediaviewer.api.serializers import (
    DownloadTokenSerializer,
    FilenameScrapeFormatSerializer,
    MessageSerializer,
    CommentSerializer,
)
from mediaviewer.models import DownloadToken
from mediaviewer.models import Message
from mediaviewer.models import FilenameScrapeFormat
from mediaviewer.models import Comment, MediaFile
from mediaviewer.log import log


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

    def get_queryset(self):
        queryset = FilenameScrapeFormat.objects.all()
        log.debug("Returning FilenameScrapeFormat objects")
        return queryset


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        queryset = Message.objects.all()
        log.debug("Returning Message objects")
        return queryset


class InferScrapersView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)
    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
    )

    def post(self, request, *args, **kwargs):
        try:
            MediaFile.objects.infer_all_scrapers()
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
