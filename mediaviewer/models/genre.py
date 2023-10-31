from django.db import models


class GenreManager(models.Manager):
    def get_movie_genres(self, limit=10):
        genres = self.filter(
            pk__in=(
                self.filter(poster__movie__isnull=False)
                .values("id")
                .annotate(genre_count=models.Count("poster__movie"))
                .order_by("-genre_count", "genre")
                .values("id")[:limit]
            )
        ).order_by("genre")

        return genres

    def get_tv_genres(self, limit=10):
        genres = self.filter(
            pk__in=(
                self.filter(poster__tv__isnull=False)
                .values("id")
                .annotate(genre_count=models.Count("poster__tv"))
                .order_by("-genre_count", "genre")
                .values("id")[:limit]
            )
        ).order_by("genre")

        return genres


class Genre(models.Model):
    genre = models.TextField(blank=False, null=False)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)

    objects = GenreManager()

    class Meta:
        app_label = "mediaviewer"
        db_table = "genre"

    def __str__(self):
        return "g: %s" % (self.genre,)

    @classmethod
    def new(cls, genre):
        existing = cls.objects.filter(genre=genre.title()).first()

        if existing:
            return existing

        new_obj = cls()
        new_obj.genre = genre.title()
        new_obj.save()
        return new_obj
