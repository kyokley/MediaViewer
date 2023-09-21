import re
from django.db import models
from .core import TimeStampModel
from .poster import Poster


class MediaFileQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        Poster.objects.filter(pk__in=self.values('poster')).delete()
        return super().delete(*args, **kwargs)


class MediaFileManager(models.Manager):
    pass


class MediaFile(TimeStampModel):
    media_path = models.ForeignKey('mediaviewer.MediaPath',
                                   null=False,
                                   on_delete=models.CASCADE)
    filename = models.CharField(null=False,
                                max_length=256)
    display_name = models.CharField(null=False,
                                         blank=True,
                                         default='',
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

    def is_tv(self):
        return bool(self.media_path.tv)

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
