from django.db import models
from django.contrib.auth.models import User

class LoginEvent(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, db_column='userid')
    datecreated = models.DateTimeField(db_column='datecreated')

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'loginevent'

    def __unicode__(self):
        return 'id: %s u: %s date: %s' % (self.id,
                                          self.user.username,
                                          self.datecreated)

