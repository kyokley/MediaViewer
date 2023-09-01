from django.db import models


class Media(models.Model):
    date_created = models.DateTimeField(
        blank=True, auto_now_add=True
    )
    date_edited = models.DateTimeField(blank=True, auto_now=True)

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
