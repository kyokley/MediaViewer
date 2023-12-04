import mock
import pytest

from django.http import HttpRequest, Http404
from mediaviewer.models.genre import Genre

from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)
from mediaviewer.views.tv import (
    tvshowsummary,
    tvshows_by_genre,
    tvshows,
)
from mediaviewer.models import TV


@pytest.mark.django_db
class TestTvShowSummary:
    @pytest.fixture(autouse=True)
    def setUp(self,
              mocker,
              create_user):
        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

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
    def setUp(self,
              mocker,
              create_user):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.files.get_object_or_404"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

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
    def setUp(self,
              mocker,
              create_user,
              create_tv_media_file,
              create_movie_media_file):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.tv.get_object_or_404"
        )

        self.mock_files_by_localpath = mocker.patch(
            "mediaviewer.views.files.File.files_by_localpath"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

        self.tv_file = create_tv_media_file()
        self.movie_file = create_movie_media_file()

        self.mock_get_object_or_404.return_value = self.tv_path
        self.mock_files_by_localpath.return_value.select_related.return_value = [
            self.tv_file
        ]

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "path": self.tv_path,
            "view": "tvshows",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "tvshows",
            "title": "Tv Local Path",
            "long_plot": "",
            "table_data_page": "ajaxtvshows",
            "table_data_filter_id": self.tv_path.id,
        }

        expected = self.mock_render.return_value
        actual = tvshows(self.request, self.tv_path.id)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(TV, pk=self.tv_path.id)
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/movies.html", expected_context
        )
