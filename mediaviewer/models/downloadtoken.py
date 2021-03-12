from django.db import models
from datetime import timedelta
from datetime import datetime
import pytz
from mediaviewer.utils import getSomewhatUniqueID
from django.conf import settings as conf_settings
from mediaviewer.models.message import Message


def _createId():
    return getSomewhatUniqueID(numBytes=16)


class DownloadToken(models.Model):
    guid = models.CharField(max_length=32, default=_createId, unique=True)
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_column='userid',
    )
    path = models.TextField(db_column='path')
    filename = models.TextField(db_column='filename')
    ismovie = models.BooleanField(db_column='ismovie')
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    displayname = models.TextField(db_column='display_name')
    file = models.ForeignKey('mediaviewer.File',
                             on_delete=models.CASCADE,
                             null=False,
                             db_column='fileid',
                             blank=True,
                             )

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'downloadtoken'

    def __str__(self):
        return 'id: %s f: %s p: %s d: %s' % (self.id,
                                             self.filename,
                                             self.path,
                                             self.datecreated)

    @property
    def isvalid(self):
        # Tokens are only valid for a certain amount of time
        refDate = self.datecreated + timedelta(
            hours=conf_settings.TOKEN_VALIDITY_LENGTH)
        return refDate > datetime.now(pytz.timezone(
            conf_settings.TIME_ZONE))

    @classmethod
    def new(cls,
            user,
            file,
            datecreated=None,
            ):
        dt = cls()
        dt.user = user
        dt.filename = file.filename
        dt.path = file.path.localpathstr
        dt.ismovie = file.isMovie()

        if not datecreated:
            datecreated = datetime.now(pytz.timezone(conf_settings.TIME_ZONE))
        dt.datecreated = datecreated

        dt.displayname = file.display_name_with_path()
        dt.file = file
        dt.save()

        number_of_stored_tokens = cls.objects.count()
        if number_of_stored_tokens > conf_settings.MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS:  # noqa
            old_token = cls.objects.order_by('id').first()
            if old_token:
                old_token.delete()

        Message.createLastWatchedMessage(user, file)
        settings = user.settings()
        settings.last_watched = file.path
        settings.save()
        return dt

    @classmethod
    def getByGUID(cls, guid):
        return cls.objects.filter(guid=guid).first()
