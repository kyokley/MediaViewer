from django.db import models
from mediaviewer.media import Media


class TV(Media):
    tvdb = models.CharField(null=False,
                            default='',
                            blank=True,
                            max_length=64)
