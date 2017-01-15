from django.db import models
from django.db import connection

class MediaGenre(models.Model):
    file = models.ForeignKey('mediaviewer.File',
                             null=True,
                             blank=True)
    path = models.ForeignKey('mediaviewer.Path',
                             null=True,
                             blank=True)
    genre = models.TextField(blank=False,
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
        if not file and not path or (path and file):
            raise ValueError('Either file or path must be defined')

        obj = cls()
        obj.file = file
        obj.path = path
        obj.genre = genre
        obj.save()
        return obj

    @classmethod
    def get_movie_genres(cls):
        with connection.cursor() as cursor:
            cursor.execute("""select genre from
                                (select genre, count(*) from mediagenre
                                 where file_id is not null
                                 group by genre
                                 order by count(*) desc
                                 limit 10
                                 ) as result
                              order by genre
                              ;""")
            rows = cursor.fetchall()

        return [row[0] for row in rows]

    @classmethod
    def get_tv_genres(cls):
        with connection.cursor() as cursor:
            cursor.execute("""select genre from
                                (select genre, count(*) from mediagenre
                                 where path_id is not null
                                 group by genre
                                 order by count(*) desc
                                 limit 10
                                 ) as result
                              order by genre
                              ;""")
            rows = cursor.fetchall()

        return [row[0] for row in rows]
