from django.db import models
from .media import Media, MediaManager, MediaQuerySet


class TVQuerySet(MediaQuerySet):
    pass


class TVManager(MediaManager):
    pass


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
