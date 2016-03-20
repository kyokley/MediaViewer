from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from mediaviewer.api.serializers import (FileSerializer,
                                         MovieFileSerializer,
                                         )
from mediaviewer.models.file import File
from mediaviewer.models.path import (Path,
                                     )
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
        serializer = FileSerializer(obj)
        return RESTResponse(serializer.data)

    def create_file_obj(self, data):
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

            newFile.clean()
            newFile.save()

            if not path.lastCreatedFileDate or path.lastCreatedFileDate < newFile.datecreated:
                path.lastCreatedFileDate = newFile.datecreated
                path.save()
            log.info('New file record created for %s' % newFile.filename)
        return newFile

    def create(self, request):
        data = request.data

        try:
            newFile = self.create_file_obj(data)
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
        data = request.data
        instance = get_object_or_404(self.queryset, pk=pk)
        instance.filename = data.get('filename', instance.filename)
        instance.skip = data.get('skip', instance.skip)
        instance.finished = data.get('finished', instance.finished)
        instance.size = data.get('size', instance.size)
        instance.hide = data.get('hide', instance.hide)
        instance._searchString = data.get('_searchString', instance._searchString)
        instance.streamable = data.get('streamable', instance.streamable)

        instance.save()

        serializer = FileSerializer(instance, partial=True)
        headers = self.get_success_headers(serializer.data)

        return RESTResponse(serializer.data,
                            status=RESTstatus.HTTP_200_OK,
                            headers=headers)

class TvFileViewSet(FileViewSet):
    queryset = File.objects.filter(path__is_movie=False)

    def create(self, request):
        try:
            data = request.data
            path = Path.objects.get(pk=data['pathid'])
            if path.is_movie:
                raise Exception('Attempting to create file for non-tv type path')

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

    def create(self, request):
        try:
            data = request.data
            path = Path.objects.get(pk=data['pathid'])
            if not path.is_movie:
                raise Exception('Attempting to create file for non-movie type path')

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

    def create_file_obj(self, data):
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
            newFile.streamable = False

            newFile.clean()
            newFile.save()

            if not path.lastCreatedFileDate or path.lastCreatedFileDate < newFile.datecreated:
                path.lastCreatedFileDate = newFile.datecreated
                path.save()
            log.info('New file record created for %s' % newFile.filename)
        return newFile

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find file with id = %s' % pk)
        obj = get_object_or_404(self.queryset, pk=pk)
        serializer = FileSerializer(obj)
        return RESTResponse(serializer.data)

