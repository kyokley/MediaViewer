from django.db import models
from mediaviewer.utils import getSomewhatUniqueID


def _createId():
    return getSomewhatUniqueID(numBytes=16)


class ApiKey(models.Model):
    key = models.CharField(max_length=32, default=_createId, unique=True)
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_column="userid",
    )
