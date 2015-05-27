from django.db import models
from datetime import timedelta
from datetime import datetime as dateObj
import pytz
from mediaviewer.utils import getSomewhatUniqueID

def _createId():
    return getSomewhatUniqueID(numBytes=16)

class DownloadToken(models.Model):
    guid = models.CharField(max_length=32, default=_createId, unique=True)
    user = models.ForeignKey('auth.User', null=False, blank=False, db_column='userid')
    path = models.TextField(db_column='path')
    filename = models.TextField(db_column='filename')
    ismovie = models.BooleanField(db_column='ismovie')
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    waitertheme = models.TextField(db_column='waiter_theme')
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
        # Tokens are only valid for 3 hours
        refDate = self.datecreated + timedelta(hours=3)
        return refDate > dateObj.now(pytz.timezone('US/Central'))

