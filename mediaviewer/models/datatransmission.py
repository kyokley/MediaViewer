from django.db import models
from decimal import Decimal
from dateutil import parser

class DataTransmission(models.Model):
    id = models.IntegerField(primary_key=True)
    datestr = models.DateField(db_column='date', blank=True)
    downloaded = models.DecimalField(null=True, max_digits=1000, decimal_places=1000, blank=True)
    class Meta:
        app_label = 'mediaviewer'
        db_table = 'datatransmission'

    @property
    def transferred(self):
        return self.downloaded

    @property
    def transferredInMBs(self):
        return Decimal(str(float(self.transferred)/1000000.0)).to_integral()

    @property
    def date(self):
        return parser.parse(self.datestr).date()

    def files(self):
        return self.file_set.all()

    def errors(self):
        return self.error_set.all()

    def __str__(self):
        return 'id: %s d: %s b: %s' % (self.id, self.date, self.transferred)

