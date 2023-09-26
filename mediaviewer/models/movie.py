from django.db import models
from .media import Media, MediaManager, MediaQuerySet


class MovieQuerySet(MediaQuerySet):
    pass


class MovieManager(MediaManager):
    pass


class Movie(Media):
    poster = models.OneToOneField('mediaviewer.Poster',
                                  null=True,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  related_name='movie')
    comments = models.ManyToManyField(
        'auth.User', through='mediaviewer.Comment')

    objects = MovieManager.from_queryset(MovieQuerySet)()

    def is_tv(self):
        return False
