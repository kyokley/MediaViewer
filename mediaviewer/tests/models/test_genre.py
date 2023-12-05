import pytest

from mediaviewer.models.genre import Genre
from mediaviewer.models import Poster


@pytest.mark.django_db
class TestGetGenres:
    @pytest.fixture(autouse=True)
    def setUp(self,
              create_tv,
              create_movie,
              create_tv_media_file,
              create_movie_media_file):
        self.action = Genre.objects.create(genre="Action")
        self.mystery = Genre.objects.create(genre="Mystery")
        self.thriller = Genre.objects.create(genre="Thriller")
        self.documentary = Genre.objects.create(genre="Documentary")
        self.comedy = Genre.objects.create(genre="Comedy")
        self.drama = Genre.objects.create(genre="Drama")
        self.history = Genre.objects.create(genre="History")

        self.tv = create_tv()
        self.movie = create_movie()

        self.tv_file1 = create_tv_media_file(tv=self.tv)
        self.tv_file2 = create_tv_media_file(tv=self.tv)
        self.tv_file3 = create_tv_media_file(tv=self.tv)
        self.tv_file4 = create_tv_media_file(tv=self.tv)

        self.movie_file1 = create_movie_media_file(movie=self.movie)
        self.movie_file2 = create_movie_media_file(movie=self.movie)
        self.movie_file3 = create_movie_media_file(movie=self.movie)
        self.movie_file4 = create_movie_media_file(movie=self.movie)

        # File posters
        Poster.objects.from_ref_obj(self.tv_file1, genres=[self.thriller, self.mystery])
        Poster.objects.from_ref_obj(self.tv_file2, genres=[self.thriller, self.action])
        Poster.objects.from_ref_obj(self.tv_file3, genres=[self.comedy, self.action])
        Poster.objects.from_ref_obj(self.tv_file4, genres=[self.drama, self.thriller])

        # Path posters
        Poster.objects.from_ref_obj(self.tv, genres=[self.action, self.mystery])
        Poster.objects.from_ref_obj(self.tv, genres=[self.thriller, self.action])
        Poster.objects.from_ref_obj(self.tv, genres=[self.comedy, self.action])
        Poster.objects.from_ref_obj(self.tv, genres=[self.drama, self.thriller])

        # Movie posters
        Poster.objects.from_ref_obj(self.movie, genres=[self.thriller, self.mystery])
        Poster.objects.from_ref_obj(self.movie, genres=[self.thriller, self.action])
        Poster.objects.from_ref_obj(self.movie, genres=[self.thriller, self.action])
        Poster.objects.from_ref_obj(self.movie, genres=[self.mystery, self.drama])

    def test_get_movie_genres(self):
        expected = [self.action, self.drama, self.mystery, self.thriller]
        actual = list(Genre.objects.get_movie_genres())
        assert expected == actual

    def test_tv_genres(self):
        expected = [self.action, self.comedy, self.drama, self.mystery, self.thriller]
        actual = list(Genre.objects.get_tv_genres())
        assert expected == actual

    def test_get_movie_genres_limit(self):
        expected = [self.action, self.thriller]
        actual = list(Genre.objects.get_movie_genres(limit=2))
        assert expected == actual

    def test_get_tv_genres_limit(self):
        expected = [self.action, self.thriller]
        actual = list(Genre.objects.get_tv_genres(limit=2))
        assert expected == actual
