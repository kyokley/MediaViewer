import re
from django.db import models
from .core import TimeStampModel, ViewableObjectMixin, ViewableManagerMixin
from .poster import Poster
from mediaviewer.utils import get_search_query
from django.urls import reverse
from .filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.log import log

yearRegex = re.compile(r"20\d{2}\D?.*$")
dvdRegex = re.compile(r"[A-Z]{2,}.*$")
formatRegex = re.compile(r"\b(xvid|avi|XVID|AVI)+\b")
punctuationRegex = re.compile(r"[^a-zA-Z0-9]+")

EPISODE = 'episode'
SEASON = 'season'

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


class MediaFileManager(models.Manager, ViewableManagerMixin):
    def infer_all_scrapers(self):
        for mf in self.all():
            mf.infer_scraper()


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
    _poster = models.OneToOneField(
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
    def poster(self):
        if self._poster is None:
            self._poster = Poster.objects.create_from_ref_obj(self)
            self._poster._populate_data()
        return self._poster

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

    def infer_scraper(self, scrapers=None):
        if self.movie:
            return

        if not scrapers:
            scrapers = FilenameScrapeFormat.objects.all()
        for scraper in scrapers:
            self.scraper = scraper
            name = self.media.name
            season = self._scraped_season()
            episode = self._scraped_episode()
            if (
                season
                and episode
                and int(episode) not in (64, 65)
            ):
                # Success!

                log.debug("Success!!!")
                log.debug(
                    f"Name: {name} Season: {season} Episode: {episode} Fullname: {self.full_name} FSid: {scraper.id}"
                )

                self.save()
                self.poster.delete()

                display_name = self.displayName()
                log.debug(f"Display Name: {display_name}")
                break
        else:
            self.scraper = None

    def url(self):
        if self.is_tv():
            return '<a href="{}">{}</a>'.format(
                reverse("mediaviewer:tvdetail", args=(self.id,)), self.media.name
            )
        else:
            return '<a href="{}">{}</a>'.format(
                reverse("mediaviewer:moviedetail", args=(self.id,)), self.full_name
            )

    def last_watched_url(self):
        if self.is_tv():
            return '<a href="{}">{}</a>'.format(
                reverse("mediaviewer:tvshows", args=(self.media.id,)), self.media.name
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

    def _scraped_season(self):
        return self._scraped_episode_or_season(SEASON)

    def _scraped_episode(self):
        return self._scraped_episode_or_season(EPISODE)

    def _scraped_episode_or_season(self, episode_or_season):
        if self.movie:
            return None

        if episode_or_season == EPISODE:
            regex = self.scraper.episodeRegex
        elif episode_or_season == SEASON:
            regex = self.scraper.seasonRegex
        else:
            raise Exception(f'Invalid episode_or_season. Got {episode_or_season}')

        res = regex.findall(
            self.filename
        )
        val = res and res[0] or None
        return val and (val.isdigit() and val.zfill(2) or None) or None

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
                f"""<input class='report' name='report-{ self.id }' value='Report' type='button' onclick="reportButtonClick('{self.id}', 'mediafile')"/>""",
            ]
        )
        return payload
