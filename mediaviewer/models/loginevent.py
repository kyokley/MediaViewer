from django.conf import settings
import pytz
from datetime import datetime
from django.db import models


class LoginEvent(models.Model):
    user = models.ForeignKey('auth.User',
                             on_delete=models.CASCADE,
                             null=False,
                             blank=False,
                             db_column='userid')
    datecreated = models.DateTimeField(db_column='datecreated')

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'loginevent'

    def __str__(self):
        return 'id: %s u: %s date: %s' % (self.id,
                                          self.user.username,
                                          self.datecreated)

    @classmethod
    def new(cls, user):
        le = cls()
        le.user = user
        le.datecreated = datetime.now(pytz.timezone(settings.TIME_ZONE))
        le.save()
        number_of_events = cls.objects.count()
        if number_of_events > settings.MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS:
            oldest_event = cls.objects.order_by('id').first()
            if oldest_event:
                oldest_event.delete()
        return le
