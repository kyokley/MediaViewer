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

    @classmethod
    def new(cls, genre):
        existing = cls.objects.filter(genre=genre.title()).first()

        if existing:
            return existing

        new_obj = cls()
        new_obj.genre = genre.title()
        new_obj.save()
        return new_obj
