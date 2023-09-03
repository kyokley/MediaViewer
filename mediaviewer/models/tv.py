from django.db import models
from mediaviewer.media import Media, MediaManager, MediaQuerySet


class TVQuerySet(MediaQuerySet):
    pass


class TVManager(MediaManager):
    pass


class TV(Media):
    tvdb = models.CharField(null=False,
                            default='',
                            blank=True,
                            max_length=64)

    objects = TVManager.from_queryset(TVQuerySet)()
