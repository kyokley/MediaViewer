import re
from pathlib import Path

from django.db import models

from mediaviewer.models import FilenameScrapeFormat
from mediaviewer.utils import get_search_query

from .core import TimeStampModel
from .poster import Poster


class MediaQuerySet(models.QuerySet):
    def search(self, search_str):
        qs = self
        if search_str:
            filename_query = get_search_query(search_str, ["name"])

            qs = qs.filter(filename_query)
        return qs

    def delete(self, *args, **kwargs):
        Poster.objects.filter(pk__in=self.values("_poster")).delete()
        return super().delete(*args, **kwargs)


class MediaManager(models.Manager):
    def from_path(self, path, name=None):
        if name is None:
            ref_name = Path(path).name
            for scraper in FilenameScrapeFormat.objects.all():
                name_regex = re.compile(scraper.nameRegex)
                res = name_regex.findall(ref_name)
                name = res and res[0] or None
                sFail = re.compile(r"\s[sS]$")

                if not name:
                    continue

                name = (
                    scraper.subPeriods
                    and name.replace(".", " ").replace("-", " ").title()
                    or name
                ).strip()

                if name and name != ref_name and not sFail.findall(name):
                    break
            else:
                name = ref_name

        obj, _ = self.get_or_create(name=name)
        obj._populate_poster() # Generate poster
        return obj, _


class Media(TimeStampModel):
    name = models.CharField(null=False,
                            blank=True,
                            max_length=256)
    finished = models.BooleanField(null=False, default=False)
    hide = models.BooleanField(null=False, default=False)
    collections = models.ManyToManyField('mediaviewer.Collection',
                                         blank=True)

    class Meta:
        abstract = True

    @property
    def poster(self):
        if self._poster is None:
            self._populate_poster()
        return self._poster

    def _populate_poster(self):
        self._poster = Poster.objects.from_ref_obj(self)
        self._poster.populate_data()

    @property
    def media_path(self):
        return self.mediapath_set.order_by("-pk").first()

    def __str__(self):
        return f"<{self.__class__.__name__} n:{self.name} f:{self.finished}>"

    def __repr__(self):
        return str(self)

    def is_movie(self):
        return not self.is_tv()

    def is_tv(self):
        raise NotImplementedError("This method must be defined by subclasses")

    def delete(self, *args, **kwargs):
        if self._poster:
            self.poster.delete()
        return super().delete(*args, **kwargs)

    def is_media_file(self):
        return False

    @property
    def full_name(self):
        return self.name

    @property
    def short_name(self):
        return self.name

    @property
    def media(self):
        return self
