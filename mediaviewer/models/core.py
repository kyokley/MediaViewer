from django.conf import settings as conf_settings
from django.db import models


class TimeStampModel(models.Model):
    date_created = models.DateTimeField(blank=True, auto_now_add=True)
    date_edited = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        abstract = True


class ViewableManagerMixin:
    def most_recent_media(self, limit=10):
        from mediaviewer.models import Poster, TV, MediaFile

        mfs = (
            MediaFile.objects.filter(media_path__tv=models.OuterRef("pk"))
            .exclude(_poster__image="")
            .order_by("-_poster__release_date", "-season", "-episode")
            .values("pk")[:1]
        )
        tvs = (
            TV.objects.filter(hide=False)
            .annotate(most_recent_show=models.Subquery(mfs))
            .values("most_recent_show")
        )
        qs = (
            Poster.objects.exclude(image="")
            .filter(models.Q(movie__hide=False) | models.Q(media_file__pk__in=tvs))
            .filter(release_date__isnull=False)
            .select_related("movie", "media_file")
            .order_by("-release_date")[:limit]
        )
        return (x.ref_obj for x in qs)


class ViewableObjectMixin:
    def mark_viewed(self, user, viewed, save=True, comment_lookup=None):
        from mediaviewer.models import Comment, MediaFile, Message

        was_created = False

        if comment_lookup is None:
            media_filter = "media_file" if isinstance(self, MediaFile) else "movie"
            comment = (
                Comment.objects.filter(user=user).filter(**{media_filter: self}).first()
            )
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

    def downloadLink(self, guid):
        if self.is_movie():
            waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.WAITER_IP_FORMAT_MOVIES}{guid}/"
        else:
            waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.WAITER_IP_FORMAT_TVSHOWS}{guid}/"

        return waiter_server

    def autoplayDownloadLink(self, guid):
        if self.is_movie():
            return None
        else:
            return f"{self.downloadLink(guid)}autoplay"

    def url(self):
        raise NotImplementedError("Method must be implemented by child classes")

    def next(self):
        raise NotImplementedError("Method must be implemented by child classes")

    def previous(self):
        raise NotImplementedError("Method must be implemented by child classes")
