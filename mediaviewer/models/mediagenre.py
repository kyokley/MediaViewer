from django.db import models

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

        if path and path.isMovie():
            raise ValueError('Only paths for tv shows are allowed to be associated with genres')

        if file and not file.isMovie():
            raise ValueError('Only files for movies are allowed to be associated with genres')

        obj = cls()
        obj.file = file
        obj.path = path
        obj.genre = genre
        obj.save()
        return obj

    @classmethod
    def get_movie_genres(cls):
        genres = cls.objects.raw('''select * from mediagenre
                                    where id in
                                    (select id from
                                        (select max(id) as id, genre, count(*) from mediagenre
                                         where file_id is not null
                                         group by genre
                                         order by count(*) desc
                                         limit 10) as result)
                                    order by genre
                                    ;''')

        return genres

    @classmethod
    def get_tv_genres(cls):
        genres = cls.objects.raw('''select * from mediagenre
                                    where id in
                                    (select id from
                                        (select max(id) as id, genre, count(*) from mediagenre
                                         where path_id is not null
                                         group by genre
                                         order by count(*) desc
                                         limit 10) as result)
                                    order by genre
                                    ;''')

        return genres

    @classmethod
    def regenerateAllGenreData(cls):
        from mediaviewer.models.posterfile import PosterFile
        from mediaviewer.models.file import File
        from mediaviewer.models.path import Path

        PosterFile.objects.all().delete()
        Path.populate_all_genres(clearExisting=True)
        File.populate_all_genres(clearExisting=True)
