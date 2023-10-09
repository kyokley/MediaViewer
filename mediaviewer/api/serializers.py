from mediaviewer.models import DownloadToken
from mediaviewer.models import Path
from mediaviewer.models import FilenameScrapeFormat
from mediaviewer.models import Message
from mediaviewer.models import PosterFile
from mediaviewer.models import UserSettings
from mediaviewer.models import VideoProgress
from mediaviewer.models import DonationSite
from mediaviewer.models import TV, Movie, MediaPath, MediaFile, Comment

from rest_framework import serializers


class DonationSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationSite
        fields = ("site_name", "url")


class DownloadTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadToken
        fields = (
            "guid",
            "userid",
            "username",
            "path",
            "filename",
            "ismovie",
            "date_created",
            "tokenid",
            "isvalid",
            "displayname",
            "tv_name",
            "videoprogresses",
            "next_id",
            "previous_id",
            "binge_mode",
            "donation_site",
            "download_link",
            "theme",
            'tv_id',
        )

    userid = serializers.IntegerField(required=True, source="user.id")
    username = serializers.SerializerMethodField()
    tokenid = serializers.IntegerField(required=True, source="id")
    tv_name = serializers.SerializerMethodField()
    videoprogresses = serializers.SerializerMethodField()
    next_id = serializers.SerializerMethodField()
    previous_id = serializers.SerializerMethodField()
    binge_mode = serializers.SerializerMethodField()
    donation_site = serializers.SerializerMethodField()
    download_link = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    tv_id = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username

    def get_tv_name(self, obj):
        tv = obj.media_file.tv if obj.media_file else None
        return tv.name if tv else None

    def get_videoprogresses(self, obj):
        return [
            x.hashed_filename
            for x in VideoProgress.objects.filter(user=obj.user).filter(media_file=obj.media_file, movie=obj.movie)
        ]

    def get_next_id(self, obj):
        next_obj = obj.media_file.next() if obj.media_file else None
        return next_obj and next_obj.id

    def get_previous_id(self, obj):
        previous_obj = obj.media_file.previous() if obj.media_file else None
        return previous_obj and previous_obj.id

    def get_binge_mode(self, obj):
        user_settings = UserSettings.getSettings(obj.user)
        return user_settings.binge_mode

    def get_donation_site(self, obj):
        donation_site = DonationSite.objects.random()
        return DonationSiteSerializer(donation_site).data

    def get_download_link(self, obj):
        movie_or_media_file = obj.movie or obj.media_file
        return movie_or_media_file.downloadLink(obj.user, obj.guid)

    def get_theme(self, obj):
        user_settings = UserSettings.getSettings(obj.user)
        return user_settings.theme

    def get_tv_id(self, obj):
        tv = obj.media_file.tv if obj.media_file else None
        return tv and tv.id


class PathSerializer(serializers.ModelSerializer):
    class Meta:
        model = Path
        fields = (
            "pk",
            "localpath",
            "remotepath",
            "server",
            "skip",
            "number_of_unwatched_shows",
            "is_movie",
            "finished",
            "short_name",
        )

    pk = serializers.ReadOnlyField()
    localpath = serializers.CharField(required=True, source="localpathstr")
    remotepath = serializers.CharField(required=True, source="remotepathstr")
    server = serializers.CharField(required=True)
    skip = serializers.BooleanField(required=True)
    number_of_unwatched_shows = serializers.SerializerMethodField("unwatched_shows")
    is_movie = serializers.BooleanField(required=True)
    finished = serializers.BooleanField(required=False)
    short_name = serializers.ReadOnlyField(source="shortName")

    def unwatched_shows(self, obj):
        request = self.context.get("request")
        if request is not None:
            return obj.number_of_unwatched_shows(request.user)
        else:
            return 0


class MediaPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaPath
        fields = (
            'path',
            'tv',
            'movie',
        )
    path = serializers.SerializerMethodField("get_path")

    def get_path(self, obj):
        return str(obj.path)


class TVSerializer(serializers.ModelSerializer):
    class Meta:
        model = TV
        fields = (
            'pk',
            'name'
            'number_of_unwatched_shows',
            'paths',
        )
        number_of_unwatched_shows = serializers.SerializerMethodField("unwatched_shows")
        paths = MediaPathSerializer(many=True,
                                    read_only=True,
                                    source='media_path_set')

    def unwatched_shows(self, obj):
        request = self.context.get("request")
        if request is not None:
            return obj.number_of_unwatched_shows(request.user)
        else:
            return 0


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = (
            'pk',
            'name',
            'path',
            "localpath",
            "filename",
            "skip",
            "finished",
            "size",
            "streamable",
            "ismovie",
            "displayname",
            "watched",
        )
        path = MediaPathSerializer(many=False,
                                   read_only=True,
                                   source='media_path_set')


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = (
            "pk",
            "path",
            "localpath",
            "filename",
            "skip",
            "finished",
            "size",
            "streamable",
            "ismovie",
            "displayname",
            "watched",
        )
    localpath = serializers.CharField(required=False, source="path.localpathstr")
    filename = serializers.CharField(required=False)
    skip = serializers.BooleanField(required=False)
    finished = serializers.BooleanField(required=False)
    size = serializers.IntegerField(required=False)
    streamable = serializers.BooleanField(required=False)
    ismovie = serializers.ReadOnlyField(source="path.is_movie")
    displayname = serializers.ReadOnlyField(source="displayName")
    watched = serializers.SerializerMethodField("get_watched")

    def get_watched(self, obj):
        request = self.context.get("request")
        if request is not None:
            uc = obj.usercomment(request.user)
            if uc and uc.viewed:
                return True
        return False


class FilenameScrapeFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilenameScrapeFormat
        fields = (
            "pk",
            "nameRegex",
            "seasonRegex",
            "episodeRegex",
            "subPeriods",
            "useSearchTerm",
        )

    pk = serializers.ReadOnlyField()
    nameRegex = serializers.CharField(required=True)
    episodeRegex = serializers.CharField(required=True)
    seasonRegex = serializers.CharField(required=True)
    subPeriods = serializers.BooleanField(required=True)
    useSearchTerm = serializers.BooleanField(required=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "pk",
            "touserid",
            "body",
            "sent",
            "level",
            "datecreated",
        )

    pk = serializers.ReadOnlyField()
    touserid = serializers.IntegerField(required=True, source="touser.id")
    body = serializers.CharField(required=True)
    sent = serializers.BooleanField(required=True)
    level = serializers.IntegerField(required=True)
    datecreated = serializers.DateTimeField(required=True)


class PosterFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosterFile
        fields = (
            "pk",
            "image",
            "plot",
            "extendedplot",
            "genre",
            "actors",
            "writer",
            "director",
            "episodename",
        )
        pk = serializers.ReadOnlyField()
        image = serializers.CharField()
        plot = serializers.CharField()
        extendedplot = serializers.CharField()
        genre = serializers.CharField()
        actors = serializers.CharField()
        writer = serializers.CharField()
        director = serializers.CharField()
        episodename = serializers.CharField()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "pk",
            "media_file",
            "movie",
            "viewed",
        )
        pk = serializers.ReadOnlyField()
        viewed = serializers.BooleanField(required=True)
