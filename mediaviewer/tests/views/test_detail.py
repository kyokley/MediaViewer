import mock
import pytest

from django.http import HttpRequest, Http404

from mediaviewer.views.detail import (
    ajaxdownloadbutton,
    ajaxsuperviewed,
    ajaxviewed,
    autoplaydownloadlink,
)
from django.contrib.auth.models import (
    Group,
    AnonymousUser,
)
from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.django_db
class TestAjaxSuperViewed:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.objects.filter", autospec=True
        )

        self.mock_HttpResponse = mocker.patch(
            "mediaviewer.views.detail.HttpResponse", autospec=True
        )

        self.mock_dumps = mocker.patch("mediaviewer.views.detail.json.dumps")

        self.token = mock.MagicMock(DownloadToken)
        self.token.isvalid = True

        self.mock_filter.return_value.first.return_value = self.token

        self.request = mock.MagicMock()
        self.request.POST = {"guid": "test_guid", "viewed": "True"}

    def test_no_token(self):
        self.mock_filter.return_value.first.return_value = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        assert expected == actual

        self.mock_dumps.assert_called_once_with(
            {"errmsg": "Token is invalid", "guid": "test_guid", "viewed": True}
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, status=400, content_type="application/json"
        )
        self.mock_filter.assert_called_once_with(guid="test_guid")
        self.mock_filter.return_value.first.assert_called_once_with()

        assert not self.token.file.markFileViewed.called

    def test_token_invalid(self):
        self.token.isvalid = False

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        assert expected == actual

        self.mock_dumps.assert_called_once_with(
            {"errmsg": "Token is invalid", "guid": "test_guid", "viewed": True}
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, status=400, content_type="application/json"
        )
        self.mock_filter.assert_called_once_with(guid="test_guid")
        self.mock_filter.return_value.first.assert_called_once_with()

        assert not self.token.file.markFileViewed.called

    def test_not_viewed(self):
        self.request.POST = {"guid": "test_guid", "viewed": "False"}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        assert expected == actual

        self.mock_dumps.assert_called_once_with(
            {"errmsg": "", "guid": "test_guid", "viewed": False}
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, status=200, content_type="application/json"
        )
        self.mock_filter.assert_called_once_with(guid="test_guid")
        self.mock_filter.return_value.first.assert_called_once_with()

        self.token.file.markFileViewed.assert_called_once_with(self.token.user, False)

    def test_viewed(self):
        self.request.POST = {"guid": "test_guid", "viewed": "True"}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        assert expected == actual

        self.mock_dumps.assert_called_once_with(
            {"errmsg": "", "guid": "test_guid", "viewed": True}
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, status=200, content_type="application/json"
        )
        self.mock_filter.assert_called_once_with(guid="test_guid")
        self.mock_filter.return_value.first.assert_called_once_with()

        self.token.file.markFileViewed.assert_called_once_with(self.token.user, True)


@pytest.mark.django_db
class TestAjaxSuperViewedResponseStatusCode:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.objects.filter", autospec=True
        )

        self.mock_dumps = mocker.patch("mediaviewer.views.detail.json.dumps")

        self.token = mock.MagicMock(DownloadToken)
        self.token.isvalid = True

        self.mock_filter.return_value.first.return_value = self.token

        self.request = mock.MagicMock()
        self.request.POST = {"guid": "test_guid", "viewed": "True"}

    def test_success(self):
        self.request.POST = {"guid": "test_guid", "viewed": "True"}

        resp = ajaxsuperviewed(self.request)
        assert resp.status_code == 200

    def test_failure(self):
        self.token.isvalid = False
        self.request.POST = {"guid": "test_guid", "viewed": "True"}

        resp = ajaxsuperviewed(self.request)
        assert resp.status_code == 400


@pytest.mark.django_db
class TestAjaxViewed:
    @pytest.fixture(autouse=True)
    def setUp(self,
              mocker,
              create_user,
              create_tv_media_file):
        self.mock_HttpResponse = mocker.patch("mediaviewer.views.detail.HttpResponse")

        self.mock_dumps = mocker.patch("mediaviewer.views.detail.json.dumps")

        self.tv_file = create_tv_media_file()

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {
            str(self.tv_file.id): "true",
        }

    def test_user_not_authenticated(self):
        self.request.user = AnonymousUser()

        expected = self.mock_HttpResponse.return_value
        actual = ajaxviewed(self.request)

        assert expected == actual
        self.mock_dumps.assert_called_once_with(
            {"errmsg": "User not authenticated. Refresh and try again."}
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_valid(self):
        expected_response = {
            "errmsg": "",
            "data": {str(self.tv_file.id): "true"},
        }

        expected = self.mock_HttpResponse.return_value
        actual = ajaxviewed(self.request)

        assert expected == actual
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )


@pytest.mark.django_db
class TestAjaxDownloadButton:
    @pytest.fixture(autouse=True)
    def setUp(self,
              mocker,
              create_user,
              create_tv_media_file):
        self.mock_HttpResponse = mocker.patch("mediaviewer.views.detail.HttpResponse")

        self.mock_dumps = mocker.patch("mediaviewer.views.detail.json.dumps")

        self.mock_downloadtoken_new = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.new"
        )

        self.mock_downloadLink = mocker.patch(
            "mediaviewer.views.detail.File.downloadLink"
        )

        self.tv_file = create_tv_media_file()

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"fileid": self.tv_file.id}

    def test_user_not_authenticated(self):
        self.request.user = AnonymousUser()

        expected = self.mock_HttpResponse.return_value
        actual = ajaxdownloadbutton(self.request)

        assert expected == actual
        self.mock_dumps.assert_called_once_with(
            {"errmsg": "User not authenticated. Refresh and try again."}
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_no_file(self):
        self.request.POST.update({"fileid": 0})
        with pytest.raises(Http404):
            ajaxdownloadbutton(self.request)

    def test_valid(self):
        expected_response = {
            "guid": self.mock_downloadtoken_new.return_value.guid,
            "isMovie": self.mock_downloadtoken_new.return_value.ismovie,
            "downloadLink": self.mock_downloadLink.return_value,
            "errmsg": "",
        }

        expected = self.mock_HttpResponse.return_value
        actual = ajaxdownloadbutton(self.request)

        assert expected == actual
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )


@pytest.mark.django_db
class TestAutoPlayDownloadLink:
    @pytest.fixture(autouse=True)
    def setUp(self,
              mocker,
              create_user,
              create_tv_media_file):
        self.mock_autoplayDownloadLink = mocker.patch(
            "mediaviewer.views.detail.File.autoplayDownloadLink"
        )

        self.mock_downloadtoken_new = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.new"
        )

        self.mock_redirect = mocker.patch("mediaviewer.views.detail.redirect")

        self.tv_file = create_tv_media_file()

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_no_file(self):
        with pytest.raises(Http404):
            autoplaydownloadlink(self.request, 0)

    def test_valid(self):
        expected = self.mock_redirect.return_value
        actual = autoplaydownloadlink(self.request, self.tv_file.id)

        assert expected == actual
        self.mock_downloadtoken_new.assert_called_once_with(self.user, self.tv_file)
        self.mock_autoplayDownloadLink.assert_called_once_with(
            self.user, self.mock_downloadtoken_new.return_value.guid
        )
        self.mock_redirect.assert_called_once_with(
            self.mock_autoplayDownloadLink.return_value
        )
