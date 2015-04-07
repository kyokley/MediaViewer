from django.db import models
from django.contrib.auth.models import User

class UserComment(models.Model):
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True)
    comment = models.TextField(blank=True)
    viewed = models.BooleanField(db_column='viewed')
    file = models.ForeignKey('File', null=False, db_column='fileid', blank=False)
    user = models.ForeignKey(User, null=False, db_column='userid', blank=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'usercomment'

    def __unicode__(self):
        return 'id: %s f: %s u: %s' % (self.id, self.file.id, self.user.id)

