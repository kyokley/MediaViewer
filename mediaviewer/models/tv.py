from django.db import models

from mediaviewer.models import Comment, MediaFile, MediaPath, Poster

from .media import Media, MediaManager, MediaQuerySet


class TVQuerySet(MediaQuerySet):
    pass


class TVManager(MediaManager):
    def from_path(self, path, name=None, tv_id=None, movie_id=None):
        if movie_id is not None:
            raise ValueError("movie_id is not allowed for TV objects")

        mp = MediaPath.objects.filter(_path=path).first()
        if mp:
            tv = mp.tv
            if not tv:
                raise ValueError(f"No tv found for the given path {path}")
        else:
            if tv_id is None:
                tv, created = super().from_path(path, name=name)
            else:
                tv = self.get(pk=tv_id)

            Poster.objects.from_ref_obj(tv)
            mp = MediaPath.objects.create(_path=path, tv=tv)

        return tv


class TV(Media):
    _poster = models.OneToOneField(
        "mediaviewer.Poster",
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        related_name="tv",
    )

    objects = TVManager.from_queryset(TVQuerySet)()

    class Meta:
        verbose_name_plural = "TV"

    def add_path(self, path):
        return MediaPath.objects.create(tv=self, _path=path)

    def is_tv(self):
        return True

    def add_episode(self, filename, display_name):
        if not self.media_path:
            raise Exception("No MediaPath exists for use")

        mf = MediaFile.objects.create(
            media_path=self.media_path, filename=filename, display_name=display_name
        )
        return mf

    def episodes(self):
        base_qs = MediaFile.objects.filter(media_path__tv=self)
        return base_qs.order_by("display_name")

    def last_created_episode_at(self):
        if not hasattr(self, "_last_created_episode_at"):
            if episodes := self.episodes().order_by("-date_created"):
                self._last_created_episode_at = episodes.values_list(
                    "date_created", flat=True
                )[0]
            else:
                self._last_created_episode_at = None
        return self._last_created_episode_at

    def number_of_unwatched_shows(self, user):
        if not user:
            return 0

        episodes = MediaFile.objects.filter(
            media_path__tv=self).filter(hide=False)
        episodes_count = episodes.count()
        viewed_count = Comment.objects.filter(
            media_file__in=episodes, user=user, viewed=True
        ).count()
        return episodes_count - viewed_count

    def ajax_row_payload(self, user):
        unwatched_count = self.number_of_unwatched_shows(user)
        poster = self.poster
        tooltip_img = (
            f"<img class='tooltip-img' src='{ poster.image.url }' />"
            if poster and poster.image
            else ""
        )
        name_html = (
            f"""<a class="img-preview" href='/mediaviewer/tvshows/{ self.id }/' data-bs-toggle="popover" data-bs-trigger="hover focus" data-container="body" data-bs-placement="auto" data-bs-custom-class="preview-tooltip" data-bs-content="{tooltip_img}">"""
            f"""{ self.name }</a>\n"""
            f'<span id="unwatched-show-badge-{ self.id }" class="badge text-bg-primary">{unwatched_count or ""}</span>'
        )
        last_created_timestamp = self.last_created_episode_at()
        if last_created_timestamp:
            timestamp_html = f"""<center><span class="hidden_span">{last_created_timestamp.isoformat()}</span>{ last_created_timestamp.date().strftime('%b %d, %Y')}</center>"""
        else:
            timestamp_html = """<center><span class="hidden_span"></span></center>"""

        payload = [
            name_html,
            timestamp_html,
        ]
        return payload
