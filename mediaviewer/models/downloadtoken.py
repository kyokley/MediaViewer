from datetime import timedelta

from django.conf import settings as conf_settings
from django.db import models
from django.utils import timezone

from mediaviewer.models.message import Message
from mediaviewer.utils import getSomewhatUniqueID


def _createId():
    return getSomewhatUniqueID(numBytes=16)


class DownloadTokenManager(models.Manager):
    def get_by_guid(self, guid):
        return self.filter(guid=guid).first()

    def from_media_file(
        self,
        user,
        media_file,
    ):
        dt = self.create(
            user=user,
            filename=media_file.filename,
            path=media_file.media_path.path,
            displayname=media_file.full_name,
            media_file=media_file,
        )
        return self._post_token_create(dt, user)

    def from_movie(
        self,
        user,
        movie,
    ):
        dt = self.create(
            user=user,
            filename=movie.name,
            path=movie.mediapath_set.first().path,
            displayname=movie.full_name,
            movie=movie,
        )
        return self._post_token_create(dt, user)

    def _post_token_create(self, dt, user):
        number_of_stored_tokens = self.count()
        if (
            number_of_stored_tokens
            > conf_settings.MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS
        ):
            old_token = self.order_by("id").first()
            if old_token:
                old_token.delete()

        Message.createLastWatchedMessage(user, dt.movie or dt.media_file)
        settings = user.settings()
        if dt.movie:
            settings.last_watched_movie = dt.movie
        if dt.media_file:
            settings.last_watched_tv = dt.media_file.tv
        settings.save()
        return dt


class DownloadToken(models.Model):
    guid = models.CharField(max_length=32, default=_createId, unique=True)
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_column="userid",
    )
    path = models.TextField(db_column="path")
    filename = models.TextField(db_column="filename")
    date_created = models.DateTimeField(blank=True, auto_now_add=True, null=True)
    displayname = models.TextField(db_column="display_name")
    media_file = models.ForeignKey(
        "mediaviewer.MediaFile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    movie = models.ForeignKey(
        "mediaviewer.Movie",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    objects = DownloadTokenManager()

    class Meta:
        app_label = "mediaviewer"
        db_table = "downloadtoken"

    def __str__(self):
        return "id: %s f: %s p: %s d: %s" % (
            self.id,
            self.filename,
            self.path,
            self.date_created,
        )

    @property
    def isvalid(self):
        # Tokens are only valid for a certain amount of time
        refDate = self.date_created + timedelta(
            hours=conf_settings.TOKEN_VALIDITY_LENGTH
        )
        return refDate > timezone.now()

    @property
    def ismovie(self):
        return bool(self.movie)

    @property
    def ref_obj(self):
        return self.media_file or self.movie
