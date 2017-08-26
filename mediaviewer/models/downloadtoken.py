from django.db import models
from datetime import timedelta
from datetime import datetime
import pytz
from mediaviewer.utils import getSomewhatUniqueID
from mysite.settings import (MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS,
                             TIME_ZONE,
                             TOKEN_VALIDITY_LENGTH)
from mediaviewer.models.message import Message

def _createId():
    return getSomewhatUniqueID(numBytes=16)

class DownloadToken(models.Model):
    guid = models.CharField(max_length=32, default=_createId, unique=True)
    user = models.ForeignKey('auth.User', null=False, blank=False, db_column='userid')
    path = models.TextField(db_column='path')
    filename = models.TextField(db_column='filename')
    ismovie = models.BooleanField(db_column='ismovie')
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    displayname = models.TextField(db_column='display_name')
    file = models.ForeignKey('mediaviewer.File',
                             null=False,
                             db_column='fileid',
                             blank=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'downloadtoken'

    def __unicode__(self):
        return 'id: %s f: %s p: %s d: %s' % (self.id,
                                             self.filename,
                                             self.path,
                                             self.datecreated)

    @property
    def isvalid(self):
        # Tokens are only valid for a certain amount of time
        refDate = self.datecreated + timedelta(hours=TOKEN_VALIDITY_LENGTH)
        return refDate > datetime.now(pytz.timezone(TIME_ZONE))

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
            datecreated = datetime.now(pytz.timezone(TIME_ZONE))
        dt.datecreated = datecreated

        dt.displayname = file.displayName()
        dt.file = file
        dt.save()

        number_of_stored_tokens = cls.objects.count()
        if number_of_stored_tokens > MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS:
            old_token = cls.objects.order_by('id').first()
            if old_token:
                old_token.delete()

        Message.createLastWatchedMessage(user, file)
        return dt

    @classmethod
    def getByGUID(cls, guid):
        return cls.objects.filter(guid=guid).first()
