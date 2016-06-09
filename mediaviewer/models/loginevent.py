from mysite.settings import MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS
from django.db import models

class LoginEvent(models.Model):
    user = models.ForeignKey('auth.User', null=False, blank=False, db_column='userid')
    datecreated = models.DateTimeField(db_column='datecreated')

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'loginevent'

    def __unicode__(self):
        return 'id: %s u: %s date: %s' % (self.id,
                                          self.user.username,
                                          self.datecreated)

    @classmethod
    def new(cls, user, datecreated):
        le = cls()
        le.user = user
        le.datecreated = datecreated
        le.save()
        number_of_events = cls.objects.count()
        if number_of_events > MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS:
            oldest_event = cls.objects.order_by('id').first()
            if oldest_event:
                oldest_event.delete()
