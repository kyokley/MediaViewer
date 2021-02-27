from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from rest_framework import viewsets
from rest_framework import status as RESTstatus
from rest_framework.response import Response as RESTResponse
from mediaviewer.api.serializers import (PathSerializer,
                                         MoviePathSerializer,
                                         TvPathSerializer,
                                         )
from mediaviewer.models.path import Path
from mediaviewer.api.permissions import IsStaffOrReadOnly

from mediaviewer.log import log
from mediaviewer.utils import query_param_to_bool


class PathViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrReadOnly,)
    queryset = Path.objects.all().order_by('id')
    serializer_class = PathSerializer

    def get_queryset(self):
        localpath = self.request.query_params.get('localpath', None)
        remotepath = self.request.query_params.get('remotepath', None)
        queryset = self.queryset
        if localpath and remotepath:
            queryset = queryset.filter(localpathstr=localpath)
            queryset = queryset.filter(remotepathstr=remotepath)
            log.debug(
                'Attempting to return path with local = %s and remote = %s' % (
                    localpath, remotepath))
        return queryset

    def retrieve(self, request, pk=None):
        log.debug('Attempting to find path with id = %s' % pk)
        obj = get_object_or_404(self.queryset, pk=pk)
        serializer = PathSerializer(obj)
        return RESTResponse(serializer.data)

    def create_path_obj(self, data):
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return serializer
        else:
            raise Exception('Invalid serializer')

    def create(self, request):
        data = request.data

        newPath = Path.objects.filter(localpathstr=data['localpath']
                                      ).filter(remotepathstr=data['remotepath']
                                               ).first()

        if not newPath:
            try:
                serializer = self.create_path_obj(data)
            except Exception as e:
                log.error(str(e))
                log.error('Path creation failed!')
                return RESTResponse(status=RESTstatus.HTTP_400_BAD_REQUEST)

            headers = self.get_success_headers(serializer.data)
            return RESTResponse(serializer.data,
                                status=RESTstatus.HTTP_201_CREATED,
                                headers=headers)
        else:
            log.info(
                'Path for %s already exists. Skipping.' % newPath.localpathstr)
            serializer = PathSerializer(newPath)
            headers = self.get_success_headers(serializer.data)

            return RESTResponse(serializer.data,
                                status=RESTstatus.HTTP_200_OK,
                                headers=headers)


class MoviePathViewSet(PathViewSet):
    queryset = Path.objects.filter(is_movie=True).order_by('id')
    serializer_class = MoviePathSerializer

    def create_path_obj(self, data):
        if not data.get('is_movie', True):
            raise Exception('Path must be of movie type')
        return super(MoviePathViewSet, self).create_path_obj(data)


class TvPathViewSet(PathViewSet):
    queryset = Path.objects.filter(is_movie=False).order_by('id')
    serializer_class = TvPathSerializer

    def create_path_obj(self, data):
        if data.get('is_movie', False):
            raise Exception('Path must be of tv type')
        return super(TvPathViewSet, self).create_path_obj(data)

    def get_queryset(self):
        queryset = super().get_queryset()

        try:
            finished = query_param_to_bool(
                self.request.query_params.get('finished')
            )
        except ValueError as e:
            raise SuspiciousOperation(str(e))

        if finished is not None:
            queryset = queryset.filter(finished=finished)

        return queryset


class DistinctTvPathViewSet(viewsets.ViewSet):
    def list(self, request):
        paths = Path.distinctShowFolders()
        serializer = TvPathSerializer((paths[key] for key in paths),
                                      many=True)
        return RESTResponse(serializer.data)
