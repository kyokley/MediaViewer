from pathlib import Path

from django.db import models

from .core import TimeStampModel

B2_URI_PREFIX = "b2://"


class MediaPath(TimeStampModel):
    _path = models.CharField(
        null=False, blank=True, max_length=1024, unique=True, db_index=True
    )
    # For B2-stored movies, the actual video file name within the path.
    # TV episodes already track their file name via MediaFile.filename.
    filename = models.CharField(null=True, blank=True, max_length=1024)
    # Subtitle file names stored alongside the media in B2 (movies only;
    # TV episodes track subtitles via MediaFile.subtitle_files).
    subtitle_files = models.JSONField(null=True, blank=True, default=list)
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
            if self.is_b2:
                return self._path
            return Path(self._path)
        else:
            return None

    @property
    def media(self):
        return self.tv or self.movie

    @property
    def is_b2(self):
        return str(self._path or "").startswith(B2_URI_PREFIX)

    @property
    def bucket(self):
        if not self.is_b2:
            return None
        return self._path[len(B2_URI_PREFIX) :].split("/", 1)[0]

    @property
    def key(self):
        if not self.is_b2:
            return None
        _, _, key = self._path[len(B2_URI_PREFIX) :].partition("/")
        return key

    def file_key(self, filename):
        key = self.key or ""
        if not key.endswith("/"):
            key = f"{key}/"
        return f"{key}{filename}"

    def presigned_url(self, filename, expires_in=None):
        from mediaviewer.b2 import get_b2_client

        return get_b2_client().generate_presigned_url(
            bucket=self.bucket,
            key=self.file_key(filename),
            expires_in=expires_in,
        )
