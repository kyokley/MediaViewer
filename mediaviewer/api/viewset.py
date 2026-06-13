from django.shortcuts import get_object_or_404
from rest_framework import permissions, views, viewsets
from rest_framework.response import Response as RESTResponse
from rest_framework import serializers
from mediaviewer.api.permissions import IsStaffReadOnlyOrCheckAPIKey

from mediaviewer.api.serializers import (
    CollectionSerializer,
    CommentSerializer,
    DownloadTokenSerializer,
    FilenameScrapeFormatSerializer,
    MessageSerializer,
    GenreSerializer,
    MCPPosterSerializer,
)
from mediaviewer.log import log
from mediaviewer.models import (
    Collection,
    Comment,
    DownloadToken,
    FilenameScrapeFormat,
    MediaFile,
    Message,
    Genre,
    Poster,
)


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


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.none()
    serializer_class = CollectionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, pk=None):
        obj = get_object_or_404(Collection.objects.all(), pk=pk)
        serializer = self.serializer_class(obj)
        return RESTResponse(serializer.data)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = Genre.objects.order_by("genre")
    serializer_class = GenreSerializer


class PosterViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffReadOnlyOrCheckAPIKey,)
    queryset = Poster.objects.all()
    serializer_class = MCPPosterSerializer

    def list(self, request):
        fields = {
            "episode_name": "episodename",
            "imdb": "imdb",
            "tmdb": "tmdb",
            "tv_id": "tv",
            "movie_id": "movie",
            "mf_id": "media_file",
        }

        posters = self.queryset
        at_least_one_filter = False
        for external_name, internal_name in fields.items():
            if val := request.query_params.get(external_name, None):
                posters = posters.filter(**{internal_name: val})
                at_least_one_filter = True

        if not at_least_one_filter:
            raise serializers.ValidationError(
                f"At least one field of '{', '.join(fields.keys())}' is required"
            )
        serializer = self.serializer_class(posters, many=True)
        return RESTResponse(serializer.data)
