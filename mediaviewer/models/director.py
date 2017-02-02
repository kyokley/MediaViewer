from django.db import models

class Director(models.Model):
    name = models.TextField(blank=False,
                            null=False)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'director'

    def __unicode__(self):
        return 'id: %s n: %s' % (self.id, self.name)
