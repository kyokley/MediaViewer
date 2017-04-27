import pytz
from mysite.settings import TIME_ZONE
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Request(models.Model):
    datecreated = models.DateTimeField(db_column='datecreated', auto_now_add=True)
    dateedited = models.DateTimeField(db_column='dateedited', auto_now=True)
    name = models.TextField(blank=True, null=False)
    done = models.BooleanField()
    user = models.ForeignKey('auth.User', null=False, db_column='userid', blank=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'request'

    def __unicode__(self):
        return 'id: %s r: %s u: %s d: %s' % (self.id, self.name, self.user.username, self.done)

    def numberOfVotes(self):
        return RequestVote.objects.filter(request=self).count()

    def canVote(self, user):
        mostRecentVote = RequestVote.objects.filter(request=self).filter(user=user).order_by('-datecreated')
        mostRecentVote = mostRecentVote and mostRecentVote[0]
        if not mostRecentVote:
            return True

        currentTime = datetime.now(pytz.timezone(TIME_ZONE))
        mostRecentVoteTime = mostRecentVote.datecreated
        refTime = mostRecentVoteTime + relativedelta(days=1)

        return currentTime >= refTime

    def getSupportingUsers(self):
        sql = '''SELECT DISTINCT u.* FROM auth_user AS u
                 INNER JOIN requestvote AS rv
                 ON rv.userid = u.id
                 WHERE rv.requestid = %s;
              '''
        return User.objects.raw(sql, params=[self.id])

    @classmethod
    def new(cls,
            name,
            user,
            done=False):
        existing = (cls.objects.filter(name=name.title())
                               .filter(done=False)
                               .first())
        if existing:
            return existing

        obj = cls()
        obj.name = name.title()
        obj.user = user
        obj.done = done
        obj.save()
        return obj

    @classmethod
    def getRequestByName(cls, name):
        existing = (cls.objects.filter(name=name.title())
                               .filter(done=False)
                               .first())
        return existing

class RequestVote(models.Model):
    request = models.ForeignKey(Request, null=True, db_column='requestid', blank=False)
    user = models.ForeignKey(User, null=False, db_column='userid', blank=False)
    datecreated = models.DateTimeField(db_column='datecreated', auto_now_add=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'requestvote'

    def __unicode__(self):
        return 'id: %s r: %s u: %s d: %s' % (self.id, self.request.name, self.user.id, self.datecreated)

    @classmethod
    def new(cls, request, user):
        obj = cls()
        obj.request = request
        obj.user = user
        obj.save()
        return obj
