from django.db import models
from django.conf import settings as conf_settings
from mediaviewer.models.usersettings import LOCAL_IP, BANGUP_IP


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

    def downloadLink(self, user, guid):
        settings = user.settings()
        if not settings or settings.ip_format == LOCAL_IP:
            if self.is_movie():
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.LOCAL_WAITER_IP_FORMAT_MOVIES}{guid}/"
            else:
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.LOCAL_WAITER_IP_FORMAT_TVSHOWS}{guid}/"
        elif settings and settings.ip_format == BANGUP_IP:
            if self.is_movie():
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.BANGUP_WAITER_IP_FORMAT_MOVIES}{guid}/"
            else:
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.BANGUP_WAITER_IP_FORMAT_TVSHOWS}{guid}/"

        return waiter_server

    def autoplayDownloadLink(self, user, guid):
        if self.is_movie():
            return None
        else:
            return self.downloadLink(user, guid) + "autoplay"
