from rest_framework import serializers

from mediaviewer.models import (
    TV,
    Collection,
    Comment,
    DonationSite,
    DownloadToken,
    FilenameScrapeFormat,
    MediaFile,
    MediaPath,
    Message,
    Movie,
    UserSettings,
    VideoProgress,
)


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
            "tv_id",
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
    isvalid = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username

    def get_isvalid(self, obj):
        return obj.isvalid

    def get_tv_name(self, obj):
        tv = obj.media_file.tv if obj.media_file else None
        return tv.name if tv else None

    def get_videoprogresses(self, obj):
        return [
            x.hashed_filename
            for x in VideoProgress.objects.filter(user=obj.user).filter(
                media_file=obj.media_file, movie=obj.movie
            )
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
        return movie_or_media_file.downloadLink(obj.guid)

    def get_theme(self, obj):
        user_settings = UserSettings.getSettings(obj.user)
        return user_settings.theme

    def get_tv_id(self, obj):
        tv = obj.media_file.tv if obj.media_file else None
        return tv and tv.id


class MediaPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaPath
        fields = (
            "pk",
            "path",
            "tv",
            "movie",
            "media_files",
            "skip",
        )

    path = serializers.SerializerMethodField("get_path")
    media_files = serializers.SerializerMethodField("get_media_files")

    def get_path(self, obj):
        return str(obj.path)

    def get_media_files(self, obj):
        return obj.mediafile_set.values_list("filename", flat=True)


class TVSerializer(serializers.ModelSerializer):
    class Meta:
        model = TV
        fields = (
            "pk",
            "name",
            "number_of_unwatched_shows",
            "media_paths",
            "finished",
        )

    number_of_unwatched_shows = serializers.SerializerMethodField("unwatched_shows")
    media_paths = serializers.SerializerMethodField("get_media_paths")

    def unwatched_shows(self, obj):
        request = self.context.get("request")
        if request is not None:
            return obj.number_of_unwatched_shows(request.user)
        else:
            return 0

    def get_media_paths(self, obj):
        return [
            dict(pk=mp["pk"], path=mp["_path"], skip=mp["skip"])
            for mp in obj.mediapath_set.order_by("-pk").values("pk", "_path", "skip")
        ]


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = (
            "pk",
            "name",
            "media_path",
            "finished",
        )

    media_path = serializers.SerializerMethodField("get_media_path")

    def get_media_path(self, obj):
        mp = obj.media_path
        return dict(pk=mp.pk, path=mp._path)


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = (
            "pk",
            "media_path",
            "filename",
            "display_name",
            "size",
            "ismovie",
            "watched",
        )

    display_name = serializers.CharField(required=False)
    size = serializers.IntegerField(required=False)
    ismovie = serializers.SerializerMethodField("get_ismovie")
    watched = serializers.SerializerMethodField("get_watched")

    def get_ismovie(self, obj):
        return bool(obj.movie)

    def get_watched(self, obj):
        request = self.context.get("request")
        if request is not None:
            uc = obj.comments.filter(user=request.user).first()
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


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = (
            "pk",
            "name",
        )
        pk = serializers.ReadOnlyField()
