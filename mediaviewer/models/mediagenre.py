from django.db import models

class MediaGenre(models.model):
    file = models.ForeignKey('mediaviewer.File',
                             null=True,
                             blank=True)
    path = models.ForeignKey('mediaviewer.Path',
                             null=True,
                             blank=True)
    genre = models.TestField(blank=False,
                             null=False)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'mediagenre'

    @classmethod
    def new(cls,
            genre,
            file=None,
            path=None):
        if not file and not path:
            raise ValueError('Either file or path must be defined')

        obj = cls()
        obj.file = file
        obj.path = path
        obj.genre = genre
        obj.save()
        return obj
