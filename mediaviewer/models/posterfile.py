from django.db import models

#TODO: Add column to track tvdb and omdb success
# Destroy failed posterfiles weekly to allow new attempts
class PosterFile(models.Model):
    file = models.ForeignKey('File', null=True, db_column='fileid', blank=True, related_name='_posterfile')
    path = models.ForeignKey('Path', null=True, db_column='pathid', blank=True, related_name='_posterfile')
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True)
    image = models.TextField(blank=True)
    plot = models.TextField(blank=True)
    extendedplot = models.TextField(blank=True)
    genre = models.TextField(blank=True)
    actors = models.TextField(blank=True)
    writer = models.TextField(blank=True)
    director = models.TextField(blank=True)
    episodename = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'posterfile'

    def __unicode__(self):
        return 'id: %s f: %s i: %s' % (self.id, self.file and self.file.filename or self.path and self.path.localpathstr, self.image)

