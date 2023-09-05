from mediaviewer.core import TimeStampModel
from django.db import models


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
    search_terms = models.CharField(null=False,
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
