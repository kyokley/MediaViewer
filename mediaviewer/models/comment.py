from django.db import models
from .core import TimeStampModel


class Comment(TimeStampModel):
    viewed = models.BooleanField(null=False,
                                 default=False)
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    media_file = models.ForeignKey(
        "mediaviewer.MediaFile",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
