from django.db import models


class TimeStampModel(models.Model):
    date_created = models.DateTimeField(
        blank=True, auto_now_add=True
    )
    date_edited = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        abstract = True
