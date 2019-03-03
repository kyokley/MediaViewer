from django.db import models


class UserCommentManager(models.Manager):
    def viewed_by_file(self, user):
        file_viewed = (
            self.filter(user=user)
            .values_list('file', 'viewed')
        )
        return dict(file_viewed)


class UserComment(models.Model):
    objects = UserCommentManager()

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

    def __str__(self):
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
