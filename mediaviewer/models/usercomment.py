from django.db import models


class UserComment(models.Model):
    datecreated = models.DateTimeField(
        db_column='datecreated',
        auto_now_add=True)
    dateedited = models.DateTimeField(db_column='dateedited', auto_now=True)
    comment = models.TextField(blank=True, null=True)
    viewed = models.BooleanField(db_column='viewed')
    file = models.ForeignKey(
        'mediaviewer.File',
        on_delete=models.CASCADE,
        null=False,
        db_column='fileid',
        blank=False)
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=False,
        db_column='userid',
        blank=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'usercomment'

    def __unicode__(self):
        return 'id: %s f: %s u: %s' % (self.id, self.file.id, self.user.id)

    @classmethod
    def new(cls, file, user, comment, viewed):
        obj = cls()
        obj.file = file
        obj.user = user
        obj.comment = comment
        obj.viewed = viewed
        obj.save()
        return obj
