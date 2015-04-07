from django.db import models
from django.contrib.auth.models import User
from mediaviewer.models.downloadtoken import DownloadToken
from django.utils import timezone

class DownloadClick(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, db_column='userid')
    filename = models.TextField(db_column='filename', blank=True)
    downloadtoken = models.ForeignKey(DownloadToken,
                                      null=False,
                                      db_column='downloadtokenid',
                                      blank=False)
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    size = models.BigIntegerField(db_column='size')

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'downloadclick'

    def __unicode__(self):
        return 'id: %s u: %s file: %s datecreated: %s' % (self.id,
                                                          self.user.username,
                                                          self.filename,
                                                          self.datecreated)

    @property
    def localdatecreated(self):
        return timezone.localtime(self.datecreated)

