import re
import itertools
from .core import TimeStampModel
from django.db import models
from mediaviewer.utils import get_search_query
from .poster import Poster
from mediaviewer.models import FilenameScrapeFormat


class MediaQuerySet(models.QuerySet):
    def search(self, search_str):
        qs = self
        if search_str:
            filename_query = get_search_query(search_str, ["name"])

            qs = qs.filter(filename_query)
        return qs

    def delete(self, *args, **kwargs):
        Poster.objects.filter(pk__in=self.values('poster')).delete()
        return super().delete(*args, **kwargs)


class MediaManager(models.Manager):
    def from_filename(self, filename, **kwargs):
        for scraper in FilenameScrapeFormat.objects.all():
            res = scraper.nameRegex.findall(
                filename
            )
            name = res and res[0] or None
            sFail = re.compile(r"\s[sS]$")
            if (
                name
                and name != filename
                and not sFail.findall(name)
            ):
                break
        else:
            name = None

        kwargs['name'] = name
        return self.create(**kwargs)

    def most_recent_media(self, limit=10):
        from mediaviewer.models import MediaFile, Movie
        recent_movies = Movie.objects.order_by('-pk')[:limit]
        recent_tv = MediaFile.objects.order_by('-pk')[:limit]
        recent_files = sorted(
            [file for file in itertools.chain(
                recent_movies, recent_tv)],
            key=lambda x: x.created)
        return recent_files[:limit]


class Media(TimeStampModel):
    name = models.CharField(null=False,
                            blank=False,
                            max_length=256)
    finished = models.BooleanField(null=False,
                                   default=False)
    _search_terms = models.CharField(null=False,
                                     default='',
                                     blank=True,
                                     max_length=256)

    class Meta:
        abstract = True

    def __str__(self):
        return f'<{self.__class__.__name__} n:{self.name} f:{self.finished}>'

    def __repr__(self):
        return str(self)

    def is_movie(self):
        return not self.is_tv()

    def is_tv(self):
        raise NotImplementedError('This method must be defined by subclasses')

    def delete(self, *args, **kwargs):
        if self.poster:
            self.poster.delete()
        return super().delete(*args, **kwargs)

    @property
    def full_name(self):
        return self.name

    @property
    def short_name(self):
        return self.name

    def _get_search_terms(self):
        return self._search_terms or self.name

    def _set_search_terms(self, val):
        self._search_terms = val

    search_terms = property(fget=_get_search_terms,
                            fset=_set_search_terms)

    @property
    def media(self):
        return self
