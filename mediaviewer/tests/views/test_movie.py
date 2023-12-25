import mock
import pytest

from django.http import HttpRequest, Http404

from mediaviewer.models.genre import Genre
from mediaviewer.views.movie import (
    movies,
    movies_by_genre,
)
from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)

@pytest.mark.django_db
class TestMovies:
    @pytest.fixture(autouse=True)
    def setUp(self,
              mocker,
              create_user,
              create_tv_media_file,
              create_movie_media_file):
        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.movie.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.movie.render")

        self.tv_file = create_tv_media_file()
        self.movie_file = create_movie_media_file()

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
    def setUp(self,
              mocker,
              create_user,
              create_tv_media_file,
              create_movie_media_file):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.movie.get_object_or_404"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.movie.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.movie.render")

        self.genre = mock.MagicMock(Genre)
        self.genre.id = 123
        self.genre.genre = "test_genre"

        self.mock_get_object_or_404.return_value = self.genre

        self.tv_file = create_tv_media_file()
        self.movie_file = create_movie_media_file()

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
