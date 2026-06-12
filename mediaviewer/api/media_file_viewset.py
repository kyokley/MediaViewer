from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import serializers

from rest_framework.response import Response
from mediaviewer.models import MediaFile, Movie
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.api.permissions import IsStaffReadOnlyOrCheckAPIKey
from mediaviewer.api.serializers import MediaFileSerializer, MCPMediaFileSerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = MediaFile.objects.order_by("id")
    serializer_class = MediaFileSerializer


class MCPMediaFileAutoplayViewSet(viewsets.ViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)

    def retrieve(self, request, pk=None):
        user = request.user
        mf = get_object_or_404(MediaFile, pk=pk)
        dt = DownloadToken.objects.from_media_file(user, mf, is_mcp=True)

        downloadlink = mf.autoplayDownloadLink(dt.guid)
        return Response({"link": downloadlink})


class MCPMovieAutoplayViewSet(viewsets.ViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)

    def retrieve(self, request, pk=None):
        user = request.user
        movie = get_object_or_404(Movie, pk=pk)
        dt = DownloadToken.objects.from_movie(user, movie, is_mcp=True)

        downloadlink = movie.downloadLink(dt.guid)
        return Response({"link": downloadlink})


class MCPMediaFileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = MediaFile.objects.filter(hide=False)
    serializer_class = MCPMediaFileSerializer

    def list(self, request):
        if "tv_id" not in request.query_params:
            raise serializers.ValidationError("'tv_id' is a required argument")

        tv_id = request.query_params["tv_id"]
        mfs = self.queryset.filter(media_path__tv=tv_id)
        serializer = self.serializer_class(mfs, many=True)
        return Response(serializer.data)
