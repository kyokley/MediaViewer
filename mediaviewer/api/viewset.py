from django.db import transaction
from django.contrib.auth.models import User
from django.utils.timezone import utc
from django.shortcuts import get_object_or_404
from datetime import datetime as dateObj
from rest_framework import viewsets, views
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from rest_framework import permissions, authentication
from mediaviewer.api.serializers import (DownloadTokenSerializer,
                                         DownloadClickSerializer,
                                         DataTransmissionSerializer,
                                         ErrorSerializer,
                                         FilenameScrapeFormatSerializer,
                                         MessageSerializer,
                                         PosterFileSerializer,
                                         UserCommentSerializer,
                                         )
from mediaviewer.models.file import File
from mediaviewer.models.path import (Path,
                                     )
from mediaviewer.models.downloadclick import DownloadClick
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.datatransmission import DataTransmission
from mediaviewer.models.error import Error
from mediaviewer.models.message import Message
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.usercomment import UserComment

from mediaviewer.log import log

class DownloadTokenViewSet(viewsets.ModelViewSet):
    queryset = DownloadToken.objects.all()
    serializer_class = DownloadTokenSerializer

    def get_queryset(self):
        queryset = DownloadToken.objects.all()
        log.debug('Returning DownloadToken objects')
        return queryset

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find token with guid = %s' % pk)
        queryset = DownloadToken.objects.filter(guid=pk)
        obj = get_object_or_404(queryset, guid=pk)
        if obj:
            log.debug('Found token. isValid: %s' % obj.isvalid)
        serializer = DownloadTokenSerializer(obj)
        return RESTResponse(serializer.data)

class DownloadClickViewSet(viewsets.ModelViewSet):
    queryset = DownloadClick.objects.all()
    serializer_class = DownloadClickSerializer

    def get_queryset(self):
        queryset = DownloadClick.objects.all()
        log.debug('Returning DownloadClick objects')
        return queryset

    def create(self, request):
        data = request.data

        try:
            with transaction.atomic():
                user = User.objects.get(pk=data['userid'])
                dt = DownloadToken.objects.get(pk=data['tokenid'])
                downloadclick = DownloadClick()
                downloadclick.user = user
                downloadclick.filename = data['filename']
                downloadclick.downloadtoken = dt
                downloadclick.datecreated = dateObj.utcnow().replace(tzinfo=utc)
                downloadclick.size = int(data['size'])

                downloadclick.clean()
                downloadclick.save()
                log.debug('New click record created for user = %s and file = %s' % (user.username, downloadclick.filename))

                serializer = DownloadClickSerializer(downloadclick)
                headers = self.get_success_headers(serializer.data)

                return RESTResponse(serializer.data,
                                    status=RESTstatus.HTTP_201_CREATED,
                                    headers=headers)
        except Exception, e:
            log.error(str(e))
            log.error('DownloadClick record creation failed!')

            return RESTResponse(None,
                                status=RESTstatus.HTTP_500_INTERNAL_SERVER_ERROR,
                                headers=None)

class DataTransmissionViewSet(viewsets.ModelViewSet):
    queryset = DataTransmission.objects.all()
    serializer_class = DataTransmissionSerializer

    def get_queryset(self):
        queryset = DataTransmission.objects.all()
        log.debug('Returning DataTransmission objects')
        return queryset

class ErrorViewSet(viewsets.ModelViewSet):
    queryset = Error.objects.all()
    serializer_class = ErrorSerializer

    def get_queryset(self):
        queryset = Error.objects.all()
        log.debug('Returning Error objects')
        return queryset

class FilenameScrapeFormatViewSet(viewsets.ModelViewSet):
    queryset = FilenameScrapeFormat.objects.all()
    serializer_class = FilenameScrapeFormatSerializer

    def get_queryset(self):
        queryset = FilenameScrapeFormat.objects.all()
        log.debug('Returning FilenameScrapeFormat objects')
        return queryset

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        queryset = Message.objects.all()
        log.debug('Returning Message objects')
        return queryset

class InferScrapersView(views.APIView):
    permission_classes = (permissions.IsAdminUser,)
    authentication_classes = (authentication.BasicAuthentication,
                              authentication.SessionAuthentication,
                              )

    def post(self, request, *args, **kwargs):
        try:
            File.inferAllScrapers()
            return RESTResponse({"success": True})
        except Exception, e:
            return RESTResponse({"success": False, "error": str(e)})

class PosterViewSetByPath(viewsets.ModelViewSet):
    queryset = PosterFile.objects.all()
    serializer_class = PosterFileSerializer

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find poster with pathid = %s' % pk)
        path = Path.objects.filter(pk=pk)
        obj = PosterFile.objects.filter(path=path)
        if obj:
            serializer = self.serializer_class(obj[0])
            return RESTResponse(serializer.data)
        else:
            return RESTResponse(None,
                                status=RESTstatus.HTTP_404_NOT_FOUND)

class PosterViewSetByFile(viewsets.ModelViewSet):
    queryset = PosterFile.objects.all()
    serializer_class = PosterFileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find poster with fileid = %s' % pk)
        file = File.objects.filter(pk=pk)
        obj = PosterFile.objects.filter(file=file)
        if obj:
            serializer = self.serializer_class(obj[0])
            return RESTResponse(serializer.data)
        else:
            return RESTResponse(None,
                                status=RESTstatus.HTTP_404_NOT_FOUND)

class UserCommentViewSet(viewsets.ModelViewSet):
    queryset = UserComment.objects.all()
    serializer_class = UserCommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = UserComment.objects.filter(user=user)
        log.debug('Returning UserComment objects')
        return queryset

    def retrieve(self, request, pk=None):
        user = request.user
        file = File.objects.get(pk=pk)
        obj = (UserComment.objects
                          .filter(user=user)
                          .filter(file=file))
        if obj:
            serializer = self.serializer_class(obj[0])
            return RESTResponse(serializer.data)
        else:
            return RESTResponse(None,
                                status=RESTstatus.HTTP_404_NOT_FOUND)
