from django.db import models
from django.contrib.auth.models import User
from datetime import datetime as dateObj
from django.utils.timezone import utc
from dateutil.relativedelta import relativedelta

class Request(models.Model):
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True)
    name = models.TextField(blank=True)
    done = models.BooleanField()
    user = models.ForeignKey(User, null=False, db_column='userid', blank=False)

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

        currentTime = dateObj.utcnow().replace(tzinfo=utc)
        mostRecentVoteTime = mostRecentVote.datecreated
        refTime = mostRecentVoteTime + relativedelta(days=1)

        return currentTime >= refTime

    def getSupportingUsers(self):
        sql = '''SELECT DISTINCT u.* FROM auth_user AS u
                 INNER JOIN requestvote AS rv
                 ON rv.userid = u.id
                 WHERE rv.requestid = %s;
              ''' % (self.id,)
        return User.objects.raw(sql)

class RequestVote(models.Model):
    request = models.ForeignKey(Request, null=True, db_column='requestid', blank=False)
    user = models.ForeignKey(User, null=False, db_column='userid', blank=False)
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'requestvote'

    def __unicode__(self):
        return 'id: %s r: %s u: %s d: %s' % (self.id, self.request.name, self.user.id, self.datecreated)
