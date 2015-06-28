from django.db import transaction
from django.contrib.auth.models import User
from django.utils.timezone import utc
from django.shortcuts import get_object_or_404
from datetime import datetime as dateObj
from rest_framework import viewsets
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from mediaviewer.api.serializers import (DownloadTokenSerializer,
                                         DownloadClickSerializer,
                                         FileSerializer,
                                         MovieFileSerializer,
                                         PathSerializer,
                                         DataTransmissionSerializer,
                                         ErrorSerializer,
                                         FilenameScrapeFormatSerializer,
                                         MessageSerializer,
                                         )
from mediaviewer.models.file import File
from mediaviewer.models.path import (Path,
                                     MOVIE_PATH_ID,
                                     )
from mediaviewer.models.downloadclick import DownloadClick
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.datatransmission import DataTransmission
from mediaviewer.models.error import Error
from mediaviewer.models.message import Message
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat

from mediaviewer.log import log

class PathViewSet(viewsets.ModelViewSet):
    queryset = Path.objects.all()
    serializer_class = PathSerializer

    def get_queryset(self):
        localpath = self.request.query_params.get('localpath', None)
        remotepath = self.request.query_params.get('remotepath', None)
        queryset = Path.objects.all()
        if localpath and remotepath:
            queryset = queryset.filter(localpathstr=localpath)
            queryset = queryset.filter(remotepathstr=remotepath)
            log.debug('Attempting to return path with local = %s and remote = %s' % (localpath, remotepath))
        return queryset

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find path with id = %s' % pk)
        queryset = Path.objects.filter(pk=pk)
        obj = get_object_or_404(queryset, pk=pk)
        serializer = PathSerializer(obj)
        return RESTResponse(serializer.data)

    def create(self, request):
        data = request.DATA

        try:
            with transaction.atomic():
                newPath = Path.objects.filter(localpathstr=data['localpath']
                            ).filter(remotepathstr=data['remotepath']
                                ).first()
                if not newPath:
                    newPath = Path()
                    newPath.localpathstr = data['localpath']
                    newPath.remotepathstr = data['remotepath']
                    newPath.server = data['server']
                    newPath.skip = data['skip']
                    newPath.clean()
                    newPath.save()
                    log.info('Created new path for %s.' % newPath.localpathstr)
                else:
                    log.info('Path for %s already exists. Skipping.' % newPath.localpathstr)
        except Exception, e:
            log.error(str(e))
            log.error('Path creation failed!')
            raise

        serializer = PathSerializer(newPath)
        headers = self.get_success_headers(serializer.data)

        return RESTResponse(serializer.data,
                            status=RESTstatus.HTTP_201_CREATED,
                            headers=headers)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def get_queryset(self):
        pathid = self.request.query_params.get('pathid', None)
        queryset = File.objects.all()
        log.debug('Returning File objects')
        if pathid:
            path = Path.objects.get(pk=pathid)
            queryset = queryset.filter(path=path)
            log.debug('Filtering file objects by pathid = %s' % pathid)
        return queryset

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find file with id = %s' % pk)
        queryset = File.objects.filter(pk=pk)
        obj = get_object_or_404(queryset, pk=pk)
        serializer = FileSerializer(obj)
        return RESTResponse(serializer.data)

    def create(self, request):
        data = request.DATA

        try:
            with transaction.atomic():
                path = Path.objects.get(pk=data['pathid'])
                newFile = File()
                newFile.path = path
                newFile.filename = data['filename']
                newFile.skip = data['skip']
                newFile.finished = data['finished']
                newFile.size = data['size']
                newFile.hide = False
                newFile._searchString = path.defaultsearchstr
                newFile.streamable = True

                currentTimeStr = str(dateObj.now())
                newFile.datecreatedstr = currentTimeStr
                newFile.dateeditedstr = currentTimeStr

                newFile.clean()
                newFile.save()
                log.info('New file record created for %s' % newFile.filename)
        except Exception, e:
            log.error(str(e))
            log.error('File creation failed!')
            raise

        serializer = FileSerializer(newFile)
        headers = self.get_success_headers(serializer.data)

        return RESTResponse(serializer.data,
                            status=RESTstatus.HTTP_201_CREATED,
                            headers=headers)

    # Implements PUT
    def update(self, request, pk=None):
        data = request.DATA
        queryset = File.objects.filter(pk=pk)

        instance = get_object_or_404(queryset, pk=pk)
        instance.filename = data.get('filename', instance.filename)
        instance.skip = data.get('skip', instance.skip)
        instance.finished = data.get('finished', instance.finished)
        instance.size = data.get('size', instance.size)
        instance.hide = data.get('hide', instance.hide)
        instance._searchString = data.get('_searchString', instance._searchString)
        instance.streamable = data.get('streamable', instance.streamable)

        currentTimeStr = str(dateObj.now())
        instance.dateeditedstr = currentTimeStr
        instance.save()

        serializer = FileSerializer(instance, partial=True)
        headers = self.get_success_headers(serializer.data)

        return RESTResponse(serializer.data,
                            status=RESTstatus.HTTP_200_OK,
                            headers=headers)


class MovieFileViewSet(viewsets.ModelViewSet):
    _MOVIE_PATH = Path.objects.get(pk=MOVIE_PATH_ID)
    queryset = File.objects.filter(path=_MOVIE_PATH)
    serializer_class = MovieFileSerializer

    def create(self, request):
        data = request.DATA

        try:
            with transaction.atomic():
                newFile = File()
                newFile.path = self._MOVIE_PATH
                newFile.filename = data['filename']
                newFile.skip = data['skip']
                newFile.finished = data['finished']
                newFile.size = data['size']
                newFile.hide = False

                currentTimeStr = str(dateObj.now())
                newFile.datecreatedstr = currentTimeStr
                newFile.dateeditedstr = currentTimeStr

                newFile.clean()
                newFile.save()

                log.info('New moviefile record created for %s' % newFile.filename)

                serializer = FileSerializer(newFile)
                headers = self.get_success_headers(serializer.data)

                return RESTResponse(serializer.data,
                                    status=RESTstatus.HTTP_201_CREATED,
                                    headers=headers)
        except Exception, e:
            log.error(str(e))
            log.error('MovieFile creation failed!')

            return RESTResponse(None,
                                status=RESTstatus.HTTP_500_INTERNAL_SERVER_ERROR,
                                headers=None)

class UnstreamableFileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.filter(streamable=False)
    serializer_class = FileSerializer

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find file with id = %s' % pk)
        obj = get_object_or_404(self.queryset, pk=pk)
        serializer = FileSerializer(obj)
        return RESTResponse(serializer.data)

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
        data = request.DATA

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
