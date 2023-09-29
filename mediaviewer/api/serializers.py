from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.error import Error
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.message import Message
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.donation_site import DonationSite

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


class MoviePathSerializer(PathSerializer):
    is_movie = serializers.BooleanField(default=True)


class TvPathSerializer(PathSerializer):
    is_movie = serializers.BooleanField(default=False)


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
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

    pk = serializers.ReadOnlyField()
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


class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Error
        fields = (
            "pk",
            "date",
            "error",
            "ignore",
            "file",
            "path",
            "datatransmission",
        )

    pk = serializers.ReadOnlyField()
    downloaded = serializers.DecimalField(
        max_digits=12, decimal_places=0, required=True
    )
    date = serializers.DateTimeField(required=True)
    error = serializers.CharField(required=True, source="errorstr")
    ignore = serializers.BooleanField(required=True)
    file = serializers.CharField(required=True)
    path = serializers.CharField(required=True)
    datatransmission = serializers.IntegerField(required=True)


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


class UserCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserComment
        fields = (
            "pk",
            "comment",
            "viewed",
        )
        pk = serializers.ReadOnlyField()
        comment = serializers.CharField()
        viewed = serializers.BooleanField(required=True)
