"""
Re-implementation of PosterFile
"""
from django.db import models
# from mediaviewer.models.genre import Genre
# from mediaviewer.models.actor import Actor
# from mediaviewer.models.writer import Writer
# from mediaviewer.models.director import Director


class Poster(models.Model):
    datecreated = models.DateTimeField(
        db_column="datecreated", blank=True, auto_now_add=True
    )
    dateedited = models.DateTimeField(db_column="dateedited", blank=True, auto_now=True)

    plot = models.TextField(blank=True, null=False, default='')
    extendedplot = models.TextField(blank=True, null=False, default='')
    genres = models.ManyToManyField("mediaviewer.Genre", blank=True)
    actors = models.ManyToManyField("mediaviewer.Actor", blank=True)
    writers = models.ManyToManyField("mediaviewer.Writer", blank=True)
    directors = models.ManyToManyField("mediaviewer.Director", blank=True)
    episodename = models.CharField(blank=True, null=False, default='', max_length=100)
    rated = models.CharField(blank=True, null=False, default='', max_length=100)
    rating = models.CharField(blank=True, null=False, default='', max_length=32)
    tmdb_id = models.CharField(blank=True, null=False, default='', max_length=32)
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    tagline = models.CharField(blank=True, null=False, default='', max_length=100)
