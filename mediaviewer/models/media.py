from mediaviewer.core import TimeStampModel
from django.db import models
from mediaviewer.utils import get_search_query
from mediaviewer.poster import Poster


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
    pass


class Media(TimeStampModel):
    name = models.CharField(null=False,
                            blank=False,
                            max_length=256)
    poster = models.ForeignKey('mediaviewer.Poster',
                               null=True,
                               on_delete=models.SET_NULL,
                               blank=True)
    finished = models.BooleanField(null=False,
                                   default=False)
    default_search = models.CharField(null=False,
                                      default='',
                                      blank=True,
                                      max_length=256)
    override_display_name = models.CharField(null=False,
                                             default='',
                                             blank=True,
                                             max_length=256)
    imdb = models.CharField(null=False,
                            default='',
                            blank=True,
                            max_length=64)

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
