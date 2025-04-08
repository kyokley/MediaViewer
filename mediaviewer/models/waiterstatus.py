from django.db import models


class WaiterStatus(models.Model):
    status = models.BooleanField(db_column="status")
    failureReason = models.TextField(db_column="failurereason")
    datecreated = models.DateTimeField(db_column="datecreated", auto_now_add=True)

    class Meta:
        app_label = "mediaviewer"
        db_table = "waiterstatus"

    def __str__(self):
        return "id: %s status: %s failureReason: %s date: %s" % (
            self.id,
            self.status,
            self.failureReason,
            self.datecreated,
        )

    @classmethod
    def new(
        cls,
        status,
        failureReason,
    ):
        obj = cls()
        obj.status = status
        obj.failureReason = failureReason
        obj.save()
        return obj

    @classmethod
    def getLastStatus(cls):
        return WaiterStatus.objects.order_by("-id").first()
