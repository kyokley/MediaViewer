from django.db import models
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import datetime as dateObj
from django.utils.timezone import utc

class Message(models.Model):
    touser = models.ForeignKey('auth.User', null=False, blank=False, db_column='touserid')
    body = models.TextField(db_column='body', blank=True)
    sent = models.BooleanField(db_column='sent', blank=False)
    level = models.IntegerField(db_column='level', blank=False)
    datecreated = models.DateTimeField(db_column='datecreated')

    levels = [DEBUG,
              INFO,
              SUCCESS,
              WARNING,
              ERROR] = [messages.DEBUG,
                        messages.INFO,
                        messages.SUCCESS,
                        messages.WARNING,
                        messages.ERROR,]
    levelDescriptions = ['Debug',
                         'Info',
                         'Success',
                         'Warning',
                         'Error']
    levelDict = dict(zip(levelDescriptions, levels))

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'message'

    def __unicode__(self):
        return 'id: %s body: %s datecreated: %s sent: %s' % (self.id, self.body, self.datecreated, self.sent)

    def localdatecreated(self):
        return timezone.localtime(self.datecreated)

    @classmethod
    def createNewMessage(cls, user, body, level=messages.SUCCESS):
        newMessage = Message()
        newMessage.touser = user
        newMessage.body = body
        newMessage.datecreated = dateObj.utcnow().replace(tzinfo=utc)
        newMessage.level = level
        newMessage.sent = False
        newMessage.save()

    @classmethod
    def createSitewideMessage(cls, body, level=messages.SUCCESS):
       users = User.objects.all()
       for user in users:
           cls.createNewMessage(user, body, level=level)

    @classmethod
    def getMessagesForUser(cls, user, sent=False):
        return Message.objects.filter(touser=user).filter(sent=sent)

    @classmethod
    def add_message(cls, request, level, body, extra_tags=''):
        messages.add_message(request, level, body, extra_tags=extra_tags)


