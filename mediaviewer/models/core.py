from django.db import models


class TimeStampModel(models.Model):
    date_created = models.DateTimeField(
        blank=True, auto_now_add=True
    )
    date_edited = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        abstract = True


class ViewableObjectMixin:
    def mark_viewed(self, user, viewed, save=True, comment_lookup=None):
        from mediaviewer.models import Comment, Message, MediaFile

        was_created = False

        if comment_lookup is None:
            media_filter = 'media_file' if isinstance(self, MediaFile) else 'movie'
            comment = Comment.objects.filter(user=user).filter(**{media_filter: self}).first()
        else:
            comment = comment_lookup.get(self)

        if comment:
            comment.viewed = viewed
            was_created = False
        else:
            comment = Comment()
            if isinstance(self, MediaFile):
                comment.media_file = self
            else:
                comment.movie = self
            comment.user = user
            comment.viewed = viewed

            was_created = True

        if save:
            comment.save()

            if not self.next():
                Message.clearLastWatchedMessage(user)
        return comment, was_created
