import pytest

from mediaviewer.models.genre import Genre


@pytest.mark.django_db
class TestGetGenres:
    @pytest.fixture(autouse=True)
    def setUp(self, create_path, create_file, create_poster_file):
        self.action = Genre.objects.create(genre="Action")
        self.mystery = Genre.objects.create(genre="Mystery")
        self.thriller = Genre.objects.create(genre="Thriller")
        self.documentary = Genre.objects.create(genre="Documentary")
        self.comedy = Genre.objects.create(genre="Comedy")
        self.drama = Genre.objects.create(genre="Drama")
        self.history = Genre.objects.create(genre="History")

        self.tv_path1 = create_path(is_movie=False)
        self.tv_path2 = create_path(is_movie=False)
        self.tv_path3 = create_path(is_movie=False)
        self.tv_path4 = create_path(is_movie=False)

        self.tv_file1 = create_file(path=self.tv_path1)
        self.tv_file2 = create_file(path=self.tv_path2)
        self.tv_file3 = create_file(path=self.tv_path3)
        self.tv_file4 = create_file(path=self.tv_path4)

        self.movie_path1 = create_path(is_movie=True)
        self.movie_path2 = create_path(is_movie=True)

        self.movie_file1 = create_file(path=self.movie_path1)
        self.movie_file2 = create_file(path=self.movie_path2)
        self.movie_file3 = create_file(path=self.movie_path1)
        self.movie_file4 = create_file(path=self.movie_path2)

        # File posters
        create_poster_file(file=self.tv_file1, genres=[self.thriller, self.mystery])
        create_poster_file(file=self.tv_file2, genres=[self.thriller, self.action])
        create_poster_file(file=self.tv_file3, genres=[self.comedy, self.action])
        create_poster_file(file=self.tv_file4, genres=[self.drama, self.thriller])

        # Path posters
        create_poster_file(path=self.tv_path1, genres=[self.action, self.mystery])
        create_poster_file(path=self.tv_path2, genres=[self.thriller, self.action])
        create_poster_file(path=self.tv_path3, genres=[self.comedy, self.action])
        create_poster_file(path=self.tv_path4, genres=[self.drama, self.thriller])

        # Movie posters
        create_poster_file(file=self.movie_file1, genres=[self.thriller, self.mystery])
        create_poster_file(file=self.movie_file2, genres=[self.thriller, self.action])
        create_poster_file(file=self.movie_file3, genres=[self.thriller, self.action])
        create_poster_file(file=self.movie_file4, genres=[self.mystery, self.drama])

    def test_get_movie_genres(self):
        expected = [self.action, self.drama, self.mystery, self.thriller]
        actual = list(Genre.get_movie_genres())
        assert expected == actual

    def test_tv_genres(self):
        expected = [self.action, self.comedy, self.drama, self.mystery, self.thriller]
        actual = list(Genre.get_tv_genres())
        assert expected == actual

    def test_get_movie_genres_limit(self):
        expected = [self.action, self.thriller]
        actual = list(Genre.get_movie_genres(limit=2))
        assert expected == actual

    def test_get_tv_genres_limit(self):
        expected = [self.action, self.thriller]
        actual = list(Genre.get_tv_genres(limit=2))
        assert expected == actual
