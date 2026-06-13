from django.db import models
from mediaviewer.utils import getSomewhatUniqueID


def _createId():
    return getSomewhatUniqueID(numBytes=24)


class ApiKey(models.Model):
    key = models.CharField(max_length=48, default=_createId, unique=True)
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_column="userid",
    )

    def __str__(self):
        return f"{self.user.username} - {self.key[:4]}"
