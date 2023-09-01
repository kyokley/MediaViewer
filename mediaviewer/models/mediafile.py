from django.db import models
from mediaviewer.core import TimeStampModel


class MediaFile(TimeStampModel):
    media_path = models.ForeignKey('mediaviewer.MediaPath',
                                   null=False,
                                   on_delete=models.CASCADE)
    filename = models.CharField(null=False,
                                max_length=256)
    override_filename = models.CharField(null=False,
                                         blank=True,
                                         default='',
                                         max_length=256)
    override_season = models.PositiveSmallIntegerField(
        null=True, blank=True)
    override_episode = models.PositiveSmallIntegerField(
        nul=True, blank=True)
    _display_name = models.CharField(null=False,
                                     default='',
                                     max_length=256)
    scraper = models.ForeignKey(
        'mediaviewer.FilenameScrapeFormat',
        null=True,
        on_delete=models.SET_NULL)
    poster = models.ForeignKey(
        'mediaviewer.Poster',
        null=True,
        on_delete=models.SET_NULL)
    skip = models.BooleanField(null=False,
                               blank=True,
                               default=False)
    size = models.BigIntegerField(null=True, blank=True)
