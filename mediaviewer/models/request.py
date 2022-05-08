import pytz
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Request(models.Model):
    datecreated = models.DateTimeField(db_column="datecreated", auto_now_add=True)
    dateedited = models.DateTimeField(db_column="dateedited", auto_now=True)
    name = models.TextField(blank=True, null=False)
    done = models.BooleanField()
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        db_column="userid",
        blank=False,
    )

    class Meta:
        app_label = "mediaviewer"
        db_table = "request"

    def __str__(self):
        return f"id: {self.id} r: {self.name} u: {self.user.username} d: {self.done}"

    def numberOfVotes(self):
        return RequestVote.objects.filter(request=self).count()

    def canVote(self, user):
        mostRecentVote = (
            RequestVote.objects.filter(request=self)
            .filter(user=user)
            .order_by("-datecreated")
        )
        mostRecentVote = mostRecentVote and mostRecentVote[0]
        if not mostRecentVote:
            return True

        currentTime = datetime.now(pytz.timezone(settings.TIME_ZONE))
        mostRecentVoteTime = mostRecentVote.datecreated
        refTime = mostRecentVoteTime + relativedelta(days=1)

        return currentTime >= refTime

    def getSupportingUsers(self):
        return User.objects.filter(requestvote__request=self)

    @classmethod
    def new(cls, name, user, done=False):
        existing = cls.objects.filter(name=name.title()).filter(done=False).first()
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
        existing = cls.objects.filter(name=name.title()).filter(done=False).first()
        return existing


class RequestVote(models.Model):
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, null=True, db_column="requestid", blank=False
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False, db_column="userid", blank=False
    )
    datecreated = models.DateTimeField(db_column="datecreated", auto_now_add=True)

    class Meta:
        app_label = "mediaviewer"
        db_table = "requestvote"

    def __str__(self):
        return f"id: {self.id} r: {self.request.name} u: {self.user.username} d: {self.datecreated}"

    @classmethod
    def new(cls, request, user):
        obj = cls()
        obj.request = request
        obj.user = user
        obj.save()
        return obj
