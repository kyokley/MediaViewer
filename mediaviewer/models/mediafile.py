import re
from django.db import models
from .core import TimeStampModel, ViewableObjectMixin
from .poster import Poster
from mediaviewer.utils import get_search_query
from django.urls import reverse


class MediaFileQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        Poster.objects.filter(pk__in=self.values('poster')).delete()
        return super().delete(*args, **kwargs)

    def search(self, search_str):
        qs = self
        if search_str:
            filename_query = get_search_query(search_str, ["display_name"])

            qs = qs.filter(filename_query)
        return qs


class MediaFileManager(models.Manager):
    pass


class MediaFile(TimeStampModel, ViewableObjectMixin):
    media_path = models.ForeignKey('mediaviewer.MediaPath',
                                   null=False,
                                   on_delete=models.CASCADE)
    filename = models.CharField(null=False,
                                max_length=256)
    display_name = models.CharField(null=False,
                                    max_length=256)
    season = models.PositiveSmallIntegerField(
        null=True, blank=True)
    episode = models.PositiveSmallIntegerField(
        null=True, blank=True)
    scraper = models.ForeignKey(
        'mediaviewer.FilenameScrapeFormat',
        null=True,
        on_delete=models.SET_NULL)
    poster = models.OneToOneField(
        'mediaviewer.Poster',
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        related_name='media_file',
    )
    hide = models.BooleanField(null=False,
                               blank=True,
                               default=False)
    size = models.BigIntegerField(null=True, blank=True)

    objects = MediaFileManager.from_queryset(MediaFileQuerySet)()

    def __str__(self):
        return f'<{self.__class__.__name__} f:{self.filename} s:{self.season} e:{self.episode}>'

    def __repr__(self):
        return str(self)

    def _get_tvdb(self):
        return self.media_path.tv.tvdb if self.media_path.tv else None

    def _set_tvdb(self, val):
        if not self.media_path.tv:
            raise ValueError(f'{self} is not a TV media file')

        self.media_path.tv.tvdb = val

    tvdb = property(fget=_get_tvdb, fset=_set_tvdb)

    @property
    def media(self):
        if not hasattr(self, '_media'):
            self._media = self.media_path.media
        return self._media

    @property
    def tv(self):
        if not hasattr(self, '_tv'):
            self._tv = self.media_path.tv
        return self._tv

    @property
    def movie(self):
        if not hasattr(self, '_movie'):
            self._movie = self.media_path.movie
        return self._movie

    def is_tv(self):
        return bool(self.tv)

    def is_movie(self):
        return not self.is_tv()

    @property
    def name(self):
        return self.display_name

    @property
    def full_name(self):
        if self.is_tv():
            return f'{self.media.name} {self.name}'
        else:
            return self.name

    @property
    def short_name(self):
        if self.is_tv() and self.season is not None and self.episode is not None:
            name = f'{self.media.short_name} S{self.season} E{self.episode}'
        else:
            name = f'{self.media.short_name}'
        return name

    def url(self):
        if self.is_tv():
            return '<a href="{}">{}</a>'.format(
                reverse("mediaviewer:tvdetail", args=(self.id,)), self.full_name
            )
        else:
            return '<a href="{}">{}</a>'.format(
                reverse("mediaviewer:moviedetail", args=(self.id,)), self.full_name
            )

    def next(self):
        if self.is_movie():
            return None
        else:
            shows = list(self.tv.episodes())
            index = shows.index(self)
            if index + 1 >= len(shows):
                return None
            else:
                return shows[index + 1]

    def previous(self):
        if self.is_movie():
            return None
        else:
            shows = list(self.tv.episodes())
            index = shows.index(self)
            if index - 1 < 0:
                return None
            else:
                return shows[index - 1]

    @property
    def search_terms(self):
        return self.media.search_terms

    @property
    def _season(self):
        if self.is_movie():
            return None

        if self.override_season is not None:
            return self.override_season

        scraped_season = self._scraped_season()
        return int(scraped_season) if scraped_season else None

    def _scraped_season(self):
        if self.override_season is None:
            if not self.scraper:
                return None

            seasonRegex = re.compile(self.scraper.seasonRegex).findall(
                self.filename
            )
            season = seasonRegex and seasonRegex[0] or None
        else:
            season = self.override_season
        return season and (season.isdigit() and season.zfill(2) or None) or None

    @property
    def _episode(self):
        if self.is_movie():
            return None

        if self.override_episode is not None:
            return self.override_episode

        scraped_episode = self._scraped_episode()
        return int(scraped_episode) if scraped_episode else None

    def _scraped_episode(self):
        if self.override_episode is None:
            if not self.scraper:
                return None

            episodeRegex = re.compile(self.scraper.episodeRegex).findall(
                self.filename
            )
            episode = episodeRegex and episodeRegex[0] or None
        else:
            episode = self.override_episode
        return episode and (episode.isdigit() and episode.zfill(2) or None) or None

    def ajax_row_payload(self, can_download, waiterstatus, user):
        poster = self.poster
        tooltip_img = (
            f"""data-bs-content="<img class='tooltip-img' src='{ poster.image.url }' />\""""
            if poster and poster.image
            else ""
        )

        payload = [
            f'<a class="img-preview" href="/mediaviewer/tvdetail/{self.id}/" data-bs-toggle="popover" data-bs-trigger="hover focus" data-container="body" {tooltip_img}>{self.display_name}</a>',
            f"""<span class="hidden_span">{self.date_created.isoformat()}</span>{self.date_created.date().strftime('%b %d, %Y')}""",
        ]

        if can_download:
            if waiterstatus:
                payload.append(
                    f"""<center><a class='btn btn-info' name='download-btn' id={self.id} target=_blank rel="noopener noreferrer" onclick="openDownloadWindow('{self.id}')">Open</a></center>"""
                )
            else:
                payload.append("Alfred is down")

        cell = """<div class="row text-center">"""

        if self.comments.filter(user=user,
                                viewed=True).exists():
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" checked onclick="ajaxTVCheckBox(['{self.id}'])" />"""
        else:
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" onclick="ajaxTVCheckBox(['{self.id}'])" />"""
        cell = f'{cell}<span id="saved-{ self.id }"></span></div>'
        payload.extend(
            [
                cell,
                f"""<input class='report' name='report-{ self.id }' value='Report' type='button' onclick="reportButtonClick('{self.id}')"/>""",
            ]
        )
        return payload
