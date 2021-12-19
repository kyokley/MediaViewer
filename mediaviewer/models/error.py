from django.db import models
from dateutil import parser
from mediaviewer.models.datatransmission import DataTransmission


class Error(models.Model):
    id = models.IntegerField(primary_key=True)
    datecreatedstr = models.DateTimeField(db_column="datecreated", blank=True)
    errorstr = models.TextField(blank=True)
    ignore = models.BooleanField(db_column="ignore")
    file = models.ForeignKey(
        "mediaviewer.File",
        on_delete=models.CASCADE,
        null=True,
        db_column="fileid",
        blank=True,
    )
    path = models.ForeignKey(
        "mediaviewer.Path",
        on_delete=models.CASCADE,
        null=True,
        db_column="pathid",
        blank=True,
    )
    datatransmission = models.ForeignKey(
        DataTransmission,
        on_delete=models.CASCADE,
        null=True,
        db_column="datatransmissionid",
        blank=True,
    )

    class Meta:
        app_label = "mediaviewer"
        db_table = "error"

    @property
    def errorStr(self):
        return self.errorstr

    @property
    def datecreated(self):
        return parser.parse(self.datecreatedstr)

    @property
    def date(self):
        return self.datecreated

    def __str__(self):
        return "id: %s e: %s d: %s" % (self.id, self.errorStr, self.date)
