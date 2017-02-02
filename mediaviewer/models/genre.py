from django.db import models

class Genre(models.Model):
    genre = models.TextField(blank=False,
                             null=False)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'genre'

    def __unicode__(self):
        return 'g: %s' % (self.genre,)

    #@classmethod
    #def new(cls, genre):
        #obj = cls()
        #obj.genre = genre.title()
        #obj.save()
        #return obj
#
    #@classmethod
    #def get_genre(cls, genre):
        #return cls.objects.filter(genre=genre.title()).first()
