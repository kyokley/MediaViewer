import mock
import pytest
from django.http import HttpRequest

from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.views.home import home


@pytest.mark.django_db
class TestHome:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_user, create_tv_media_file):
        self.mock_most_recent_files = mocker.patch(
            "mediaviewer.views.home.MediaFile.objects.most_recent_media"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.home.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.home.render")

        self.user = create_user()

        self.tv_file = create_tv_media_file(filename="tv.file")

        self.mock_most_recent_files.return_value = [self.tv_file]

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_with_greeting(self):
        SiteGreeting.new("test_greeting")

        expected_context = {
            "greeting": "test_greeting",
            "active_page": "home",
            "title": "Home",
            "carousel_files": [self.tv_file],
        }

        expected = self.mock_render.return_value
        actual = home(self.request)

        assert expected == actual
        self.mock_most_recent_files.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/home.html", expected_context
        )

    def test_no_greeting(self):
        expected_context = {
            "greeting": "Check out the new downloads!",
            "active_page": "home",
            "carousel_files": [self.tv_file],
            "title": "Home",
        }

        expected = self.mock_render.return_value
        actual = home(self.request)

        assert expected == actual
        self.mock_most_recent_files.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/home.html", expected_context
        )
