from rest_framework import serializers

from mediaviewer.models import (
    Poster,
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
    Genre,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("genre",)


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
            "original_filename",
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
            "subtitle_files",
            "theme",
            "tv_id",
            "is_mcp",
            "og_title",
            "og_type",
            "og_url",
            "og_image",
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
    subtitle_files = serializers.SerializerMethodField()
    original_filename = serializers.SerializerMethodField()
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
        if not obj.isvalid:
            return None
        movie_or_media_file = obj.movie or obj.media_file
        return movie_or_media_file.downloadLink(obj.guid)

    def get_subtitle_files(self, obj):
        if not obj.isvalid:
            return []
        if obj.media_file:
            media_file = obj.media_file
            media_path = media_file.media_path
            if media_path.is_b2:
                if media_file.b2_uuid:
                    return [
                        media_path.b2_filename_presigned_url(filename)
                        for filename in (media_file.subtitle_files or [])
                    ]
                return [
                    media_path.presigned_url(filename)
                    for filename in (media_file.subtitle_files or [])
                ]
        elif obj.movie:
            media_path = obj.movie.mediapath_set.order_by("-pk").first()
            if media_path and media_path.is_b2:
                media_files = MediaFile.objects.filter(
                    media_path=media_path,
                    filename=media_path.filename,
                    b2_uuid__isnull=False,
                )
                if media_files.count() == 1:
                    media_file = media_files.get()
                    return [
                        media_path.b2_filename_presigned_url(filename)
                        for filename in (media_file.subtitle_files or [])
                    ]
                return [
                    media_path.presigned_url(filename)
                    for filename in (media_path.subtitle_files or [])
                ]
        return []

    def get_original_filename(self, obj):
        if obj.media_file:
            return obj.media_file.filename
        if obj.movie:
            media_path = obj.movie.mediapath_set.order_by("-pk").first()
            return media_path.filename if media_path else obj.movie.name
        return None

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
            "b2_upload_prefix",
            "bucket",
            "filename",
            "subtitle_files",
            "tv",
            "movie",
            "media_files",
            "skip",
        )

    path = serializers.SerializerMethodField("get_path")
    b2_upload_prefix = serializers.ReadOnlyField()
    bucket = serializers.ReadOnlyField()
    media_files = serializers.SerializerMethodField("get_media_files")

    def get_path(self, obj):
        return str(obj.path)

    def get_media_files(self, obj):
        return obj.mediafile_set.values_list("filename", flat=True)

    def update(self, instance, validated_data):
        filename = validated_data.get("filename", instance.filename)
        if (
            instance.movie_id
            and filename != instance.filename
            and instance.mediafile_set.filter(b2_uuid__isnull=False).exists()
        ):
            raise serializers.ValidationError(
                {"filename": "Cannot change filename for a published UUID movie."}
            )
        return super().update(instance, validated_data)


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


class MCPTVSerializer(TVSerializer):
    class Meta:
        model = TV
        fields = (
            "pk",
            "name",
            "genres",
        )

    genres = serializers.SerializerMethodField("get_genres")

    def get_genres(self, obj):
        if obj._poster is None:
            return []
        return [g.genre for g in obj._poster.genres.all()]


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
        return dict(
            pk=mp.pk,
            path=mp._path,
            filename=mp.filename,
            b2_upload_prefix=mp.b2_upload_prefix,
            bucket=mp.bucket,
        )


class MCPMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = (
            "pk",
            "name",
        )


class MediaFileSerializer(serializers.ModelSerializer):
    b2_uuid = serializers.UUIDField(required=False, allow_null=True, validators=[])

    class Meta:
        model = MediaFile
        fields = (
            "pk",
            "media_path",
            "filename",
            "b2_uuid",
            "display_name",
            "size",
            "subtitle_files",
            "ismovie",
            "watched",
        )
        validators = []

    display_name = serializers.CharField(required=False)
    size = serializers.IntegerField(required=False)
    ismovie = serializers.SerializerMethodField("get_ismovie")
    watched = serializers.SerializerMethodField("get_watched")

    @staticmethod
    def _schedule_episode_enrichment(media_file):
        from django.db import transaction

        if (
            not media_file.is_tv()
            or media_file.season is None
            or media_file.episode is None
            or media_file._poster_id is None
        ):
            return

        poster = Poster.objects.get(pk=media_file._poster_id)
        if poster.episodename and poster.extendedplot and poster.release_date:
            return

        poster_id = poster.pk

        def enrich_episode_metadata():
            Poster.objects.get(pk=poster_id).populate_data()
            media_file.refresh_from_db(fields=("display_name",))

        transaction.on_commit(enrich_episode_metadata, robust=True)

    def create(self, validated_data):
        from django.db import IntegrityError, transaction
        from rest_framework.exceptions import ValidationError

        b2_uuid = validated_data.get("b2_uuid")
        if b2_uuid is None:
            return super().create(validated_data)
        try:
            with transaction.atomic():
                media_path = MediaPath.objects.select_for_update().get(
                    pk=validated_data["media_path"].pk
                )
                validated_data["media_path"] = media_path
                filename = validated_data["filename"]
                existing = MediaFile.objects.filter(b2_uuid=b2_uuid).first()
                if existing:
                    expected = {
                        "media_path_id": media_path.pk,
                        "filename": filename,
                        "size": validated_data.get("size"),
                        "subtitle_files": validated_data.get("subtitle_files") or [],
                    }
                    if all(
                        getattr(existing, key) == value
                        for key, value in expected.items()
                    ):
                        return existing
                    raise ValidationError(
                        {"b2_uuid": "UUID already belongs to another upload."}
                    )

                matches = MediaFile.objects.filter(
                    media_path=media_path, filename=filename
                )
                if matches.count() > 1:
                    raise ValidationError(
                        {
                            "filename": "Multiple MediaFiles match this path and filename."
                        }
                    )
                if media_path.movie_id:
                    if media_path.filename and media_path.filename != filename:
                        raise ValidationError(
                            {"filename": "Movie path already published."}
                        )
                    if MediaFile.objects.filter(
                        media_path=media_path, b2_uuid__isnull=False
                    ).exists():
                        raise ValidationError(
                            {"b2_uuid": "Movie already has a primary UUID file."}
                        )
                    media_path.filename = filename
                    media_path.subtitle_files = (
                        validated_data.get("subtitle_files") or []
                    )
                    media_path.save(update_fields=("filename", "subtitle_files"))

                match = matches.first()
                if match and match.b2_uuid is None:
                    match.b2_uuid = b2_uuid
                    match.size = validated_data.get("size")
                    match.subtitle_files = validated_data.get("subtitle_files") or []
                    match.save(update_fields=("b2_uuid", "size", "subtitle_files"))
                    match.ensure_episode_fields()
                    self._schedule_episode_enrichment(match)
                    return match
                if match:
                    raise ValidationError(
                        {
                            "filename": "A UUID upload is already published for this filename."
                        }
                    )
                media_file = super().create(validated_data)
                media_file.ensure_episode_fields()
                self._schedule_episode_enrichment(media_file)
                return media_file
        except IntegrityError as error:
            raise ValidationError(
                {"b2_uuid": "UUID conflicts with another upload."}
            ) from error

    def update(self, instance, validated_data):
        if instance.b2_uuid is None and validated_data.get("b2_uuid") is not None:
            raise serializers.ValidationError(
                {"b2_uuid": "Use POST to publish a UUID B2 upload."}
            )
        if instance.b2_uuid:
            for field in ("b2_uuid", "media_path", "filename"):
                if field not in validated_data:
                    continue
                current = (
                    instance.media_path_id
                    if field == "media_path"
                    else getattr(instance, field)
                )
                value = (
                    validated_data[field].pk
                    if field == "media_path"
                    else validated_data[field]
                )
                if value != current:
                    raise serializers.ValidationError(
                        {field: "Cannot change identity of a published B2 upload."}
                    )
        return super().update(instance, validated_data)

    def get_ismovie(self, obj):
        return bool(obj.movie)

    def get_watched(self, obj):
        request = self.context.get("request")
        if request is not None:
            uc = obj.comments.filter(user=request.user).first()
            if uc and uc.viewed:
                return True
        return False


class MCPMediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = (
            "pk",
            "display_name",
        )


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


class PosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poster
        fields = (
            "pk",
            "tv",
            "movie",
            "media_file",
            "genres",
            "actors",
            "writers",
            "directors",
            "episodename",
            "tmdb",
            "imdb",
            "plot",
            "extendedplot",
        )
        tv = TVSerializer(read_only=True)
        movie = MovieSerializer(read_only=True)
        mediafile = MediaFileSerializer(read_only=True)


class MCPPosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poster
        fields = (
            "pk",
            "tv",
            "movie",
            "media_file",
            "genres",
            "actors",
            "writers",
            "directors",
            "episodename",
            "tmdb",
            "imdb",
            "plot",
            "extendedplot",
        )
        tv = MCPTVSerializer(read_only=True)
        movie = MCPMovieSerializer(read_only=True)
        media_file = MCPMediaFileSerializer(read_only=True)
