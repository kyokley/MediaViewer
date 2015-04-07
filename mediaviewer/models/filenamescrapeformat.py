from django.db import models

class FilenameScrapeFormat(models.Model):
    nameRegex = models.TextField(db_column='nameregex', blank=True, null=True)
    seasonRegex = models.TextField(db_column='seasonregex', blank=True, null=True)
    episodeRegex = models.TextField(db_column='episoderegex', blank=True, null=True)
    subPeriods = models.BooleanField(db_column='subperiods', blank=True, null=False)
    useSearchTerm = models.BooleanField(db_column='usesearchterm', blank=True, null=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'filenamescrapeformat'

    def __unicode__(self):
        return 'id: %s n: %s s: %s e: %s subPeriods: %s useSearchTerm: %s' % (self.id, self.nameRegex, self.seasonRegex, self.episodeRegex, self.subPeriods, self.useSearchTerm)

