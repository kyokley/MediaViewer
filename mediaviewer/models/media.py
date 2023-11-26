import re
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
    def from_filename(self, filename):
        for scraper in FilenameScrapeFormat.objects.all():
            res = scraper.nameRegex.findall(
                filename
            )
            name = res and res[0] or None
            sFail = re.compile(r"\s[sS]$")

            if not name:
                continue

            name = (
                (
                    scraper.subPeriods
                    and name.replace(".", " ").replace("-", " ").title()
                    or name
                ).strip()
            )

            if (
                name
                and name != filename
                and not sFail.findall(name)
            ):
                break
        else:
            name = filename

        return self.get_or_create(name=name)


class Media(TimeStampModel):
    name = models.CharField(null=False,
                            blank=False,
                            max_length=256)
    finished = models.BooleanField(null=False,
                                   default=False)
    hide = models.BooleanField(null=False,
                               default=False)

    class Meta:
        abstract = True

    @property
    def media_path(self):
        return self.mediapath_set.order_by('-pk').first()

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

    @property
    def media(self):
        return self
