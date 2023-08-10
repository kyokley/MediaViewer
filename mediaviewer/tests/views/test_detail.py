import mock
import pytest

from django.http import HttpRequest, Http404

from mediaviewer.views.detail import (
    ajaxdownloadbutton,
    ajaxsuperviewed,
    ajaxviewed,
    filesdetail,
    downloadlink,
    autoplaydownloadlink,
)
from django.contrib.auth.models import (
    Group,
    AnonymousUser,
)
from mediaviewer.models.usersettings import (
    UserSettings,
    LOCAL_IP,
    BANGUP_IP,
)
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.usercomment import UserComment


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
class TestFilesDetail:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.detail.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.detail.render")

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.tv_path.tvdb_id = None

        self.tv_file = File.new("tv.file", self.tv_path)
        self.tv_file.override_filename = "test str"
        self.tv_file.override_season = "3"
        self.tv_file.override_episode = "5"

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_no_comment(self):
        expected_context = {
            "file": self.tv_file,
            "posterfile": self.tv_file.posterfile,
            "comment": "",
            "skip": self.tv_file.skip,
            "finished": self.tv_file.finished,
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "viewed": False,
            "can_download": True,
            "file_size": None,
            "active_page": "tvshows",
            "title": "Tv Local Path",
            "displayName": "tv.file",
        }
        expected = self.mock_render.return_value
        actual = filesdetail(self.request, self.tv_file.id)

        assert expected == actual
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/filesdetail.html", expected_context
        )

    def test_comment(self):
        usercomment = UserComment()
        usercomment.file = self.tv_file
        usercomment.user = self.user
        usercomment.viewed = True
        usercomment.comment = "test_comment"
        usercomment.save()

        expected_context = {
            "file": self.tv_file,
            "posterfile": self.tv_file.posterfile,
            "comment": "test_comment",
            "skip": self.tv_file.skip,
            "finished": self.tv_file.finished,
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "viewed": True,
            "can_download": True,
            "file_size": None,
            "active_page": "tvshows",
            "title": "Tv Local Path",
            "displayName": "tv.file",
        }
        expected = self.mock_render.return_value
        actual = filesdetail(self.request, self.tv_file.id)

        assert expected == actual
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/filesdetail.html", expected_context
        )


@pytest.mark.django_db
class TestAjaxViewed:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_HttpResponse = mocker.patch("mediaviewer.views.detail.HttpResponse")

        self.mock_dumps = mocker.patch("mediaviewer.views.detail.json.dumps")

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.tv_path.tvdb_id = None

        self.tv_file = File.new("tv.file", self.tv_path)
        self.tv_file.override_filename = "test str"
        self.tv_file.override_season = "3"
        self.tv_file.override_episode = "5"

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False)
        self.user.settings().force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {
            "fileid": self.tv_file.id,
            "viewed": "true",
        }

    def test_no_file(self):
        self.request.POST.update({"fileid": 0, "viewed": "true"})
        with pytest.raises(Http404):
            ajaxviewed(self.request)

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
            "fileid": self.tv_file.id,
            "viewed": True,
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
    def setUp(self, mocker):
        self.mock_HttpResponse = mocker.patch("mediaviewer.views.detail.HttpResponse")

        self.mock_dumps = mocker.patch("mediaviewer.views.detail.json.dumps")

        self.mock_downloadtoken_new = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.new"
        )

        self.mock_downloadLink = mocker.patch(
            "mediaviewer.views.detail.File.downloadLink"
        )

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.tv_path.tvdb_id = None

        self.tv_file = File.new("tv.file", self.tv_path)
        self.tv_file.override_filename = "test str"
        self.tv_file.override_season = "3"
        self.tv_file.override_episode = "5"

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False)
        self.user.settings().force_password_change = False

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
class TestDownloadlink:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_downloadLink = mocker.patch(
            "mediaviewer.views.detail.File.downloadLink"
        )

        self.mock_downloadtoken_new = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.new"
        )

        self.mock_redirect = mocker.patch("mediaviewer.views.detail.redirect")

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.tv_path.tvdb_id = None

        self.tv_file = File.new("tv.file", self.tv_path)
        self.tv_file.override_filename = "test str"
        self.tv_file.override_season = "3"
        self.tv_file.override_episode = "5"

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False)
        self.user.settings().force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_no_file(self):
        with pytest.raises(Http404):
            downloadlink(self.request, 0)

    def test_valid(self):
        expected = self.mock_redirect.return_value
        actual = downloadlink(self.request, self.tv_file.id)

        assert expected == actual
        self.mock_downloadtoken_new.assert_called_once_with(self.user, self.tv_file)
        self.mock_downloadLink.assert_called_once_with(
            self.user, self.mock_downloadtoken_new.return_value.guid
        )
        self.mock_redirect.assert_called_once_with(self.mock_downloadLink.return_value)


@pytest.mark.django_db
class TestAutoPlayDownloadLink:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_autoplayDownloadLink = mocker.patch(
            "mediaviewer.views.detail.File.autoplayDownloadLink"
        )

        self.mock_downloadtoken_new = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.new"
        )

        self.mock_redirect = mocker.patch("mediaviewer.views.detail.redirect")

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.tv_path.tvdb_id = None

        self.tv_file = File.new("tv.file", self.tv_path)
        self.tv_file.override_filename = "test str"
        self.tv_file.override_season = "3"
        self.tv_file.override_episode = "5"

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False)
        self.user.settings().force_password_change = False

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
