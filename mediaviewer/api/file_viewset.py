from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from mediaviewer.api.serializers import (FileSerializer,
                                         MovieFileSerializer,
                                         )
from mediaviewer.models.file import File
from mediaviewer.log import log

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def get_queryset(self):
        pathid = self.request.query_params.get('pathid', None)
        queryset = self.queryset
        log.debug('Returning File objects')
        if pathid:
            queryset = queryset.filter(path__id=pathid)
            log.debug('Filtering file objects by pathid = %s' % pathid)
        return queryset

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find file with id = %s' % pk)
        queryset = self.queryset
        obj = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer_class(obj)
        return RESTResponse(serializer.data)

    def validate_path(self, serializer):
        pass

    def create_file_obj(self, data):
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            self.validate_path(serializer)
        else:
            raise Exception('Invalid serializer')

        newFile = serializer.instance
        path = newFile.path
        if not path.lastCreatedFileDate or path.lastCreatedFileDate < newFile.datecreated:
            path.lastCreatedFileDate = newFile.datecreated
            path.save()
        log.info('New file record created for %s' % newFile.filename)
        return serializer

    def create(self, request):
        data = request.data

        try:
            with transaction.atomic():
                serializer = self.create_file_obj(data)
        except Exception, e:
            log.error(str(e))
            log.error('File creation failed!')
            return RESTResponse(status=RESTstatus.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(serializer.data)
        return RESTResponse(serializer.data,
                            status=RESTstatus.HTTP_201_CREATED,
                            headers=headers)

    # Implements PUT
    def update(self, request, pk=None):
        data = request.data
        instance = get_object_or_404(self.queryset, pk=pk)

        serializer = self.serializer_class(instance, data=data)
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)

            return RESTResponse(serializer.data,
                                status=RESTstatus.HTTP_200_OK,
                                headers=headers)
        else:
            return RESTResponse(status=RESTstatus.HTTP_400_BAD_REQUEST)

class TvFileViewSet(FileViewSet):
    queryset = File.objects.filter(path__is_movie=False)

    def validate_path(self, serializer):
        if serializer.instance.path.is_movie:
            raise Exception('Attempting to use a movie path with a tv obj')

    def create(self, request):
        try:
            return super(TvFileViewSet, self).create(request)
        except Exception, e:
            log.error(str(e))
            log.error('TvFile creation failed!')

            return RESTResponse(None,
                                status=RESTstatus.HTTP_500_INTERNAL_SERVER_ERROR,
                                headers=None)

class MovieFileViewSet(FileViewSet):
    queryset = File.objects.filter(path__is_movie=True)
    serializer_class = MovieFileSerializer

    def validate_path(self, serializer):
        if not serializer.instance.path.is_movie:
            raise Exception('Attempting to use a tv path with a movie obj')

    def create(self, request):
        try:
            return super(MovieFileViewSet, self).create(request)
        except Exception, e:
            log.error(str(e))
            log.error('MovieFile creation failed!')

            return RESTResponse(None,
                                status=RESTstatus.HTTP_500_INTERNAL_SERVER_ERROR,
                                headers=None)

class UnstreamableFileViewSet(FileViewSet):
    queryset = File.objects.filter(streamable=False)
    serializer_class = FileSerializer
