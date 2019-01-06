from django.db import models
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import datetime as dateObj
from django.utils.timezone import utc

REGULAR = 'regular'
LAST_WATCHED = 'last_watched'

CONTINUE_MESSAGE = 'Continue watching {}?'


class Message(models.Model):
    MESSAGE_TYPES = ((REGULAR, 'Regular'),
                     (LAST_WATCHED, 'Last Watched'),
                     )
    touser = models.ForeignKey('auth.User',
                               on_delete=models.CASCADE,
                               null=False,
                               blank=False,
                               db_column='touserid')
    body = models.TextField(db_column='body', blank=True)
    sent = models.BooleanField(db_column='sent', blank=False)
    level = models.IntegerField(db_column='level', blank=False)
    datecreated = models.DateTimeField(db_column='datecreated')
    message_type = models.CharField(max_length=15,
                                    choices=MESSAGE_TYPES,
                                    default=REGULAR,
                                    null=False,
                                    blank=True)

    levels = [DEBUG,
              INFO,
              SUCCESS,
              WARNING,
              ERROR] = [messages.DEBUG,
                        messages.INFO,
                        messages.SUCCESS,
                        messages.WARNING,
                        messages.ERROR,
                        ]
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
        return 'id: %s body: %s datecreated: %s sent: %s' % (
                self.id,
                self.body,
                self.datecreated,
                self.sent)

    def localdatecreated(self):
        return timezone.localtime(self.datecreated)

    @classmethod
    def createNewMessage(cls,
                         user,
                         body,
                         level=messages.SUCCESS,
                         message_type=REGULAR):
        newMessage = Message()
        newMessage.touser = user
        newMessage.body = body
        newMessage.datecreated = dateObj.utcnow().replace(tzinfo=utc)
        newMessage.level = level
        newMessage.sent = False
        newMessage.message_type = message_type
        newMessage.save()

    @classmethod
    def createSitewideMessage(cls, body, level=messages.SUCCESS):
        users = User.objects.all()
        for user in users:
            cls.createNewMessage(user, body, level=level)

    @classmethod
    def createLastWatchedMessage(cls, user, file, level=messages.WARNING):
        if file.isTVShow():
            body = CONTINUE_MESSAGE.format(file.path.url())
        else:
            body = CONTINUE_MESSAGE.format(file.url())

        old_messages = (cls.objects.filter(touser=user)
                                   .filter(sent=False)
                                   .filter(message_type=LAST_WATCHED)
                                   .all())

        for old_message in old_messages:
            old_message.delete()

        cls.createNewMessage(user,
                             body,
                             level=level,
                             message_type=LAST_WATCHED)

    @classmethod
    def clearLastWatchedMessage(cls, user):
        for message in cls.getMessagesForUser(user,
                                              message_type=LAST_WATCHED):
            message.delete()

    @classmethod
    def getMessagesForUser(cls, user, sent=False, message_type=REGULAR):
        return (cls.objects.filter(touser=user)
                           .filter(sent=sent)
                           .filter(message_type=message_type))

    @classmethod
    def add_message(cls, request, level, body, extra_tags=''):
        messages.add_message(request, level, body, extra_tags=extra_tags)
