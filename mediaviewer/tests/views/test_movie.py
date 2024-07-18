import mock
import pytest
from django.http import Http404, HttpRequest

from mediaviewer.models.genre import Genre
from mediaviewer.models.usersettings import BANGUP_IP, LOCAL_IP
from mediaviewer.views.movie import movies, movies_by_genre


@pytest.mark.django_db
class TestMovies:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_user, create_tv_media_file, create_movie_media_file, create_movie):
        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.movie.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.movie.render")

        self.tv_file = create_tv_media_file()
        self.movie = create_movie()
        self.movie_file = create_movie_media_file(movie=self.movie)

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "view": "movies",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "movies",
            "title": "Movies",
            "table_data_page": "ajaxmovierows",
            "carousel_files": [self.movie],
        }
        expected = self.mock_render.return_value
        actual = movies(self.request)

        assert expected == actual
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context,
            self.request,
            includeMessages=True,
        )
        self.mock_render.assert_called_once_with(
            self.request,
            "mediaviewer/movies.html",
            expected_context,
        )


@pytest.mark.django_db
class TestMovieByGenre404:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        with pytest.raises(Http404):
            movies_by_genre(self.request, 100)


@pytest.mark.django_db
class TestMoviesByGenre:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_user, create_tv_media_file, create_movie_media_file, create_movie):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.movie.get_object_or_404"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.movie.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.movie.render")

        self.genre = Genre.objects.create(genre="test_genre")

        self.mock_get_object_or_404.return_value = self.genre

        self.tv_file = create_tv_media_file()

        self.movie = create_movie()
        self.movie_file = create_movie_media_file(movie=self.movie)

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "view": "movies",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "movies",
            "title": "Movies: test_genre",
            "table_data_page": "ajaxmoviesbygenrerows",
            "table_data_filter_id": self.genre.id,
            "carousel_files": [],
        }

        expected = self.mock_render.return_value
        actual = movies_by_genre(self.request, self.genre.id)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(
            Genre,
            pk=self.genre.id,
        )
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context,
            self.request,
            includeMessages=True,
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/movies.html", expected_context
        )
