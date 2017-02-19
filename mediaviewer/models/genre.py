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

    @classmethod
    def get_movie_genres(cls):
        sql = '''
select * from genre
where genre.id in
(select id from
    (select g.id, count(*) from genre as g
    inner join posterfile_genres as pg
    on pg.genre_id = g.id
    inner join posterfile as p
    on p.id = pg.posterfile_id
    inner join file as f
    on f.id = p.fileid
    inner join path
    on path.id = f.pathid
    where path.ismovie = 't'
    group by g.id
    order by count(*) desc
    limit 10) as agg_genre
)
order by genre.genre desc;
        '''

        genres = cls.objects.raw(sql);
        return genres

    @classmethod
    def get_tv_genres(cls):
        sql = '''
select * from genre
where genre.id in
(select id from
    (select g.id, count(*) from genre as g
    inner join posterfile_genres as pg
    on pg.genre_id = g.id
    inner join posterfile as p
    on p.id = pg.posterfile_id
    inner join file as f
    on f.id = p.fileid
    inner join path
    on path.id = f.pathid
    where path.ismovie = 'f'
    group by g.id
    order by count(*) desc
    limit 10) as agg_genre
)
order by genre.genre desc;
        '''

        genres = cls.objects.raw(sql);
        return genres
