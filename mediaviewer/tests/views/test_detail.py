from datetime import timedelta

import mock
import pytest
from django.http import HttpRequest
from django.urls import resolve, reverse

from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.views.detail import ajaxsuperviewed


@pytest.mark.django_db
class TestAjaxSuperViewed:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv_media_file, create_movie, create_user, client):
        self.user = create_user()
        self.client = client

        self.tv_mf = create_tv_media_file()
        self.movie = create_movie()

        self.request = mock.MagicMock()
        self.payload = {"guid": "test_guid", "viewed": "True"}

        self.url = reverse("mediaviewer:ajaxsuperviewed")

    def test_no_token(self):
        self.client.force_login(self.user)

        self.payload.pop("guid")
        resp = self.client.post(self.url, data=self.payload)
        json_data = resp.json()

        assert resp.status_code == 400

        assert json_data == {"errmsg": "Token is invalid", "guid": "", "viewed": True}

    @pytest.mark.parametrize("use_movie", (True, False))
    def test_token_invalid(self, use_movie):
        self.client.force_login(self.user)

        if use_movie:
            dt = DownloadToken.objects.from_movie(self.user, self.movie)
        else:
            dt = DownloadToken.objects.from_media_file(self.user, self.tv_mf)

        dt.date_created = dt.date_created - timedelta(days=1)
        dt.save()

        self.payload["guid"] = dt.guid

        resp = self.client.post(self.url, data=self.payload)

        assert resp.status_code == 400

        json_data = resp.json()

        assert json_data == {
            "errmsg": "Token is invalid",
            "guid": dt.guid,
            "viewed": True,
        }

    @pytest.mark.parametrize("use_movie", (True, False))
    @pytest.mark.parametrize("viewed", (True, False))
    def test_viewed(self, use_movie, viewed):
        self.client.force_login(self.user)

        if use_movie:
            obj = self.movie
            dt = DownloadToken.objects.from_movie(self.user, self.movie)
        else:
            obj = self.tv_mf
            dt = DownloadToken.objects.from_media_file(self.user, self.tv_mf)
        self.payload["guid"] = dt.guid
        self.payload["viewed"] = str(viewed)

        resp = self.client.post(self.url, data=self.payload)

        assert resp.status_code == 200
        json_data = resp.json()

        assert json_data == {"errmsg": "", "guid": dt.guid, "viewed": viewed}

        assert obj.comments.filter(user=self.user, viewed=True).exists() == viewed


@pytest.mark.django_db
class TestAjaxSuperViewedResponseStatusCode:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            "mediaviewer.views.detail.DownloadToken.objects.filter", autospec=True
        )

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
@pytest.mark.parametrize("use_movie", (True, False))
@pytest.mark.parametrize("viewed", (True, False))
class TestAjaxViewed:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, create_tv_media_file, create_movie, client):
        self.user = create_user()
        self.client = client

        self.tv_mf = create_tv_media_file()
        self.movie = create_movie()

        self.url = reverse("mediaviewer:ajaxviewed")

    def test_user_not_authenticated(self, use_movie, viewed):
        if use_movie:
            payload = {"movies": {self.movie.pk: viewed}}
        else:
            payload = {"media_files": {self.tv_mf.pk: viewed}}
        resp = self.client.post(self.url, payload, content_type="application/json")

        assert resp.status_code == 400
        json_data = resp.json()

        assert json_data == {"errmsg": "User not authenticated. Refresh and try again."}

    def test_viewed(self, use_movie, viewed):
        if use_movie:
            obj = self.movie
            payload = {"movies": {self.movie.pk: viewed}}
        else:
            obj = self.tv_mf
            payload = {"media_files": {self.tv_mf.pk: viewed}}

        self.client.force_login(self.user)

        resp = self.client.post(self.url, payload, content_type="application/json")

        assert resp.status_code == 200

        assert obj.comments.filter(user=self.user, viewed=True).exists() == viewed


@pytest.mark.django_db
@pytest.mark.parametrize("use_movie", (True, False))
class TestAjaxDownloadButton:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, create_tv_media_file, create_movie, client):
        self.client = client

        self.tv_mf = create_tv_media_file()
        self.movie = create_movie()

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"fileid": self.tv_mf.id}

        self.url = reverse("mediaviewer:ajaxdownloadbutton")

    def test_user_not_authenticated(self, use_movie):
        if use_movie:
            payload = {"movie_id": self.movie.pk}
        else:
            payload = {"mf_id": self.tv_mf.pk}

        resp = self.client.post(self.url, payload)

        assert resp.status_code == 400
        json_data = resp.json()

        assert json_data == {"errmsg": "User not authenticated. Refresh and try again."}

    def test_valid(self, use_movie):
        if use_movie:
            payload = {"movie_id": self.movie.pk}
        else:
            payload = {"mf_id": self.tv_mf.pk}

        self.client.force_login(self.user)
        resp = self.client.post(self.url, payload)

        assert resp.status_code == 200
        json_data = resp.json()

        dt_guid = json_data["guid"]
        dt = DownloadToken.objects.get_by_guid(dt_guid)

        assert dt.ismovie == use_movie
        assert dt.user == self.user
        assert dt.isvalid


@pytest.mark.django_db
class TestAutoPlayDownloadLink:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, create_tv_media_file, client, settings):
        settings.WAITER_IP_FORMAT_TVSHOWS = "example.com/tv/"

        self.client = client
        self.tv_mf = create_tv_media_file()

        self.user = create_user()
        self.url = reverse(
            "mediaviewer:autoplaydownloadlink", kwargs=dict(mf_id=self.tv_mf.pk)
        )

    def test_user_is_unauthenticated(self):
        resp = self.client.post(self.url)

        assert resp.status_code == 302

        resolve_match = resolve(resp.url)
        assert resolve_match.url_name == "signin"

    def test_valid(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url)

        assert resp.status_code == 302
        assert "example.com" in resp.url
