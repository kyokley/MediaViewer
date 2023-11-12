from django.db import models
from .media import Media, MediaManager, MediaQuerySet
from mediaviewer.models import MediaFile, Comment, MediaPath


class TVQuerySet(MediaQuerySet):
    pass


class TVManager(MediaManager):
    def create(self,
               *args,
               path=None,
               **kwargs):
        tv = super().create(*args, **kwargs)
        if path:
            mp, created = MediaPath.objects.get_or_create(
                _path=path,
                defaults=dict(tv=tv))
        return tv


class TV(Media):
    poster = models.OneToOneField('mediaviewer.Poster',
                                  null=True,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  related_name='tv')

    objects = TVManager.from_queryset(TVQuerySet)()

    class Meta:
        verbose_name_plural = "TV"

    def is_tv(self):
        return True

    def add_episode(self, filename, display_name):
        media_path = self.mediapath_set.order_by('-pk').first()
        if not media_path:
            raise Exception('No MediaPath exists for use')

        mf = MediaFile.objects.create(
            media_path=media_path,
            filename=filename,
            display_name=display_name
        )
        return mf

    def episodes(self):
        base_qs = MediaFile.objects.filter(media_path__tv=self)
        return base_qs.order_by('display_name')

    def last_created_episode_at(self):
        if not hasattr(self, '_last_created_episode_at'):
            if episodes := self.episodes().order_by('-date_created'):
                self._last_created_episode_at = episodes.values_list('date_created', flat=True)[0]
            else:
                self._last_created_episode_at = None
        return self._last_created_episode_at

    def number_of_unwatched_shows(self, user):
        if not user:
            return 0

        episodes = MediaFile.objects.filter(media_path__tv=self)
        episodes_count = episodes.count()
        viewed_count = Comment.objects.filter(media_file__in=episodes,
                                              user=user,
                                              viewed=True).count()
        return episodes_count - viewed_count

    def ajax_row_payload(self, user):
        unwatched_count = self.number_of_unwatched_shows(user)
        poster = self.poster
        tooltip_img = (
            f"<img class='tooltip-img' src='{ poster.image.url }' />"
            if poster and poster.image
            else ""
        )
        payload = [
            (
                f"""<a class="img-preview" href='/mediaviewer/tvshows/{ self.id }/' data-bs-toggle="popover" data-bs-trigger="hover focus" data-container="body" data-bs-content="{tooltip_img}">"""
                f"""{ self.name }</a>\n"""
                f'<span id="unwatched-show-badge-{ self.id }" class="badge text-bg-primary">{unwatched_count or ""}</span>'
            ),
            f"""<span class="hidden_span">{self.last_created_episode_at().isoformat()}</span>{ self.last_created_episode_at().date().strftime('%b %d, %Y')}""",
        ]
        return payload
