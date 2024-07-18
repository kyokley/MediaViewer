import mock
import pytest
from django.http import Http404, HttpRequest

from mediaviewer.models import TV
from mediaviewer.models.genre import Genre
from mediaviewer.models.usersettings import BANGUP_IP, LOCAL_IP
from mediaviewer.views.tv import tvshows, tvshows_by_genre, tvshowsummary


@pytest.mark.django_db
class TestTvShowSummary:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_user):
        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.tv.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.tv.render")

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "active_page": "tvshows",
            "title": "TV Shows",
            "table_data_page": "ajaxtvshowssummary",
            "table_data_filter_id": "",
        }

        expected = self.mock_render.return_value
        actual = tvshowsummary(self.request)

        assert expected == actual
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/tvsummary.html", expected_context
        )


@pytest.mark.django_db
class TestTvShowByGenre404:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        with pytest.raises(Http404):
            tvshows_by_genre(self.request, 100)


@pytest.mark.django_db
class TestTvShowsByGenre:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_user):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.tv.get_object_or_404"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.tv.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.tv.render")

        self.genre = mock.MagicMock(Genre)
        self.genre.id = 123
        self.genre.genre = "test_genre"

        self.mock_get_object_or_404.return_value = self.genre

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "active_page": "tvshows",
            "title": "TV Shows: test_genre",
            "table_data_page": "ajaxtvshowsbygenre",
            "table_data_filter_id": self.genre.id,
        }

        expected = self.mock_render.return_value
        actual = tvshows_by_genre(self.request, self.genre.id)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(Genre, pk=self.genre.id)
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/tvsummary.html", expected_context
        )


@pytest.mark.django_db
class TestTvShow404:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        with pytest.raises(Http404):
            tvshows(self.request, 100)


@pytest.mark.django_db
class TestTvShows:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_user, create_tv_media_file, create_movie_media_file):
        mocker.patch("mediaviewer.models.poster.Poster.populate_data")

        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.tv.get_object_or_404"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.tv.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.tv.render")

        self.tv_file = create_tv_media_file()
        self.movie_file = create_movie_media_file()

        self.mock_get_object_or_404.return_value = self.tv_file.tv

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "tv": self.tv_file.tv,
            "view": "tvshows",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "tvshows",
            "title": self.tv_file.tv.name,
            "long_plot": "",
            "table_data_page": "ajaxtvshows",
            "table_data_filter_id": self.tv_file.tv.id,
        }

        expected = self.mock_render.return_value
        actual = tvshows(self.request, self.tv_file.tv.id)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(TV, pk=self.tv_file.tv.id)
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/tvshows.html", expected_context
        )
