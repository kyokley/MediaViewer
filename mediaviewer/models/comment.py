from django.db import models
from .core import TimeStampModel


class Comment(TimeStampModel):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    media_file = models.ForeignKey(
        "mediaviewer.MediaFile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
    )
    movie = models.ForeignKey(
        "mediaviewer.Movie",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
    )
    viewed = models.BooleanField(null=False,
                                 default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'media_file'),
                name='unique_user_media_file'),
            models.UniqueConstraint(
                fields=('user', 'movie'),
                name='unique_user_movie'),
        ]
