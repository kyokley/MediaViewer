from pathlib import Path

from django.db import models

from .core import TimeStampModel


class MediaPath(TimeStampModel):
    _path = models.CharField(null=False,
                             blank=True,
                             max_length=256,
                             unique=True,
                             db_index=True)
    skip = models.BooleanField(null=False, blank=True, default=False)
    tv = models.ForeignKey(
        "mediaviewer.TV", null=True, on_delete=models.CASCADE, blank=True
    )
    movie = models.ForeignKey(
        "mediaviewer.Movie", null=True, on_delete=models.CASCADE, blank=True
    )

    def __str__(self):
        return f"<MediaPath {self.path}>"

    def __repr__(self):
        return str(self)

    @property
    def path(self):
        if self._path:
            return Path(self._path)
        else:
            return None

    @property
    def media(self):
        return self.tv or self.movie
