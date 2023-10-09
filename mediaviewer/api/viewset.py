from django.shortcuts import get_object_or_404
from rest_framework import viewsets, views
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from rest_framework import permissions, authentication
from mediaviewer.api.serializers import (
    DownloadTokenSerializer,
    FilenameScrapeFormatSerializer,
    MessageSerializer,
    PosterFileSerializer,
    CommentSerializer,
    PathSerializer,
)
from mediaviewer.models import File
from mediaviewer.models import (
    Path,
)
from mediaviewer.models import DownloadToken
from mediaviewer.models import Message
from mediaviewer.models import FilenameScrapeFormat
from mediaviewer.models import PosterFile
from mediaviewer.models import Comment
from mediaviewer.log import log


class DownloadTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DownloadTokenSerializer

    def retrieve(self, request, pk=None):
        log.debug(f"Attempting to find token with guid = {pk}")
        queryset = DownloadToken.objects.filter(guid=pk)
        obj = get_object_or_404(queryset, guid=pk)
        if obj:
            log.debug(f"Found token. isValid: {obj.isvalid}")
        serializer = DownloadTokenSerializer(obj)
        return RESTResponse(serializer.data)

    def create(self, request):
        user = request.user
        file_id = request.data["file_id"]
        file = get_object_or_404(File.objects.filter(hide=False), pk=file_id)
        token = DownloadToken.new(user, file)
        serializer = DownloadTokenSerializer(token)
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
            File.inferAllScrapers()
            return RESTResponse({"success": True})
        except Exception as e:
            return RESTResponse({"success": False, "error": str(e)})

    def get(self, request, *args, **kwargs):
        title = request.GET.get("title")

        if not title:
            return RESTResponse(None, status=RESTstatus.HTTP_404_NOT_FOUND)

        log.debug(f"Attempting to scrape title = {title}")
        path = FilenameScrapeFormat.path_for_filename(title)

        if path:
            serializer = PathSerializer(path)
            return RESTResponse(serializer.data)
        else:
            return RESTResponse(None, status=RESTstatus.HTTP_404_NOT_FOUND)


class PosterViewSetByPath(viewsets.ModelViewSet):
    queryset = PosterFile.objects.all()
    serializer_class = PosterFileSerializer

    def retrieve(self, request, pk=None):
        log.debug(f"Attempting to find poster with pathid = {pk}")
        path = Path.objects.filter(pk=pk)
        obj = PosterFile.objects.filter(path=path)
        if obj:
            serializer = self.serializer_class(obj[0])
            return RESTResponse(serializer.data)
        else:
            return RESTResponse(None, status=RESTstatus.HTTP_404_NOT_FOUND)


class PosterViewSetByFile(viewsets.ModelViewSet):
    queryset = PosterFile.objects.all()
    serializer_class = PosterFileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, pk=None):
        log.debug(f"Attempting to find poster with fileid = {pk}")
        file = File.objects.filter(pk=pk)
        obj = PosterFile.objects.filter(file=file)
        if obj:
            serializer = self.serializer_class(obj[0])
            return RESTResponse(serializer.data)
        else:
            return RESTResponse(None, status=RESTstatus.HTTP_404_NOT_FOUND)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.none()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(user=user)
        log.debug("Returning UserComment objects")
        return queryset
