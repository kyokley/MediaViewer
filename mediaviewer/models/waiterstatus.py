from django.db import models

class WaiterStatus(models.Model):
    status = models.BooleanField(db_column='status')
    failureReason = models.TextField(db_column='failurereason')
    datecreated = models.DateTimeField(db_column='datecreated')

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'waiterstatus'

    def __unicode__(self):
        return 'id: %s status: %s failureReason: %s date: %s' % (self.id, self.status, self.failureReason, self.datecreated)

    @classmethod
    def getLastStatus(cls):
        obj = WaiterStatus.objects.order_by('-id')
        return obj and obj[0] or None

