from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from mediaviewer.api.serializers import PathSerializer
from mediaviewer.models.path import Path

from mediaviewer.log import log

class PathViewSet(viewsets.ModelViewSet):
    queryset = Path.objects.all()
    serializer_class = PathSerializer

    def get_queryset(self):
        localpath = self.request.query_params.get('localpath', None)
        remotepath = self.request.query_params.get('remotepath', None)
        queryset = self.queryset
        if localpath and remotepath:
            queryset = queryset.filter(localpathstr=localpath)
            queryset = queryset.filter(remotepathstr=remotepath)
            log.debug('Attempting to return path with local = %s and remote = %s' % (localpath, remotepath))
        return queryset

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find path with id = %s' % pk)
        obj = get_object_or_404(self.queryset, pk=pk)
        serializer = PathSerializer(obj)
        return RESTResponse(serializer.data)

    def create_path_obj(self, data):
        with transaction.atomic():
            newPath = Path()
            newPath.localpathstr = data['localpath']
            newPath.remotepathstr = data['remotepath']
            newPath.server = data['server']
            newPath.skip = True if data['skip'].upper() == 'TRUE' else False
            newPath.is_movie = True if data['is_movie'].upper() == 'TRUE' else False
            newPath.clean()
            newPath.save()
            log.info('Created new path for %s.' % newPath.localpathstr)
        return newPath

    def create(self, request):
        data = request.data

        newPath = Path.objects.filter(localpathstr=data['localpath']
                    ).filter(remotepathstr=data['remotepath']
                        ).first()

        if not newPath:
            try:
                newPath = self.create_path_obj(data)
            except Exception, e:
                log.error(str(e))
                log.error('Path creation failed!')
                raise
        else:
            log.info('Path for %s already exists. Skipping.' % newPath.localpathstr)
            serializer = PathSerializer(newPath)
            headers = self.get_success_headers(serializer.data)

            return RESTResponse(serializer.data,
                                status=RESTstatus.HTTP_200_OK,
                                headers=headers)

        serializer = PathSerializer(newPath)
        headers = self.get_success_headers(serializer.data)

        return RESTResponse(serializer.data,
                            status=RESTstatus.HTTP_201_CREATED,
                            headers=headers)

class MoviePathViewSet(PathViewSet):
    queryset = Path.objects.filter(is_movie=True)
    serializer_class = PathSerializer

    def create_path_obj(self, data):
        with transaction.atomic():
            newPath = Path()
            newPath.localpathstr = data['localpath']
            newPath.remotepathstr = data['remotepath']
            newPath.server = data['server']
            newPath.skip = True if data['skip'].upper() == 'TRUE' else False
            newPath.is_movie = True
            newPath.clean()
            newPath.save()
            log.info('Created new path for %s.' % newPath.localpathstr)
        return newPath

class TvPathViewSet(PathViewSet):
    queryset = Path.objects.filter(is_movie=False)
    serializer_class = PathSerializer

    def create_path_obj(self, data):
        with transaction.atomic():
            newPath = Path()
            newPath.localpathstr = data['localpath']
            newPath.remotepathstr = data['remotepath']
            newPath.server = data['server']
            newPath.skip = True if data['skip'].upper() == 'TRUE' else False
            newPath.is_movie = False
            newPath.clean()
            newPath.save()
            log.info('Created new path for %s.' % newPath.localpathstr)
        return newPath
