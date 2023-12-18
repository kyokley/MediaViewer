import mock
import pytest

from datetime import timedelta
from django.http import HttpRequest, Http404
from django.urls import reverse

from mediaviewer.views.detail import (
    ajaxdownloadbutton,
    ajaxsuperviewed,
    autoplaydownloadlink,
)
from django.contrib.auth.models import (
    Group,
)
from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.django_db
class TestAjaxSuperViewed:
    @pytest.fixture(autouse=True)
    def setUp(self,
              create_tv_media_file,
              create_movie,
              create_user,
              client):
        self.user = create_user()
        self.client = client

        self.tv_mf = create_tv_media_file()
        self.movie = create_movie()

        self.request = mock.MagicMock()
        self.payload = {"guid": "test_guid", "viewed": "True"}

        self.url = reverse('mediaviewer:ajaxsuperviewed')

    def test_no_token(self):
        self.client.force_login(self.user)

        self.payload.pop('guid')
        resp = self.client.post(self.url,
                                data=self.payload)
        json_data = resp.json()

        assert resp.status_code == 400

        assert json_data == {"errmsg": "Token is invalid", "guid": "", "viewed": True}

    @pytest.mark.parametrize(
        'use_movie',
        (True, False))
    def test_token_invalid(self, use_movie):
        self.client.force_login(self.user)

        if use_movie:
            dt = DownloadToken.objects.from_movie(self.user,
                                                  self.movie)
        else:
            dt = DownloadToken.objects.from_media_file(self.user,
                                                       self.tv_mf)

        dt.date_created = dt.date_created - timedelta(days=1)
        dt.save()

        self.payload['guid'] = dt.guid

        resp = self.client.post(self.url,
                                data=self.payload)

        assert resp.status_code == 400

        json_data = resp.json()

        assert json_data == {"errmsg": "Token is invalid",
                             "guid": dt.guid,
                             "viewed": True}

    @pytest.mark.parametrize(
        'use_movie',
        (True, False))
    @pytest.mark.parametrize(
        'viewed',
        (True, False))
    def test_viewed(self, use_movie, viewed):
        self.client.force_login(self.user)

        if use_movie:
            obj = self.movie
            dt = DownloadToken.objects.from_movie(self.user,
                                                  self.movie)
        else:
            obj = self.tv_mf
            dt = DownloadToken.objects.from_media_file(self.user,
                                                       self.tv_mf)
        self.payload['guid'] = dt.guid
        self.payload['viewed'] = str(viewed)

        resp = self.client.post(self.url,
                                data=self.payload)

        assert resp.status_code == 200
        json_data = resp.json()

        assert json_data == {"errmsg": "",
                             "guid": dt.guid,
                             "viewed": viewed}

        assert obj.comments.filter(user=self.user,
                                    viewed=True).exists() == viewed


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
@pytest.mark.parametrize(
    'use_movie',
    (True, False))
@pytest.mark.parametrize(
    'viewed',
    (True, False))
class TestAjaxViewed:
    @pytest.fixture(autouse=True)
    def setUp(self,
              create_user,
              create_tv_media_file,
              create_movie,
              client):
        self.user = create_user()
        self.client = client

        self.tv_mf = create_tv_media_file()
        self.movie = create_movie()

        self.url = reverse('mediaviewer:ajaxviewed')

    def test_user_not_authenticated(self,
                                    use_movie,
                                    viewed):
        if use_movie:
            payload = {'movies': {
                self.movie.pk: viewed}}
        else:
            payload = {'media_files': {
                self.tv_mf.pk: viewed}}
        resp = self.client.post(self.url,
                                payload,
                                content_type='application/json')

        assert resp.status_code == 400
        json_data = resp.json()

        assert json_data == {"errmsg": "User not authenticated. Refresh and try again."}

    def test_viewed(self,
                    use_movie,
                    viewed):
        if use_movie:
            obj = self.movie
            payload = {'movies': {
                self.movie.pk: viewed}}
        else:
            obj = self.tv_mf
            payload = {'media_files': {
                self.tv_mf.pk: viewed}}

        self.client.force_login(self.user)

        resp = self.client.post(self.url,
                                payload,
                                content_type='application/json')

        assert resp.status_code == 200

        assert obj.comments.filter(user=self.user,
                                    viewed=True).exists() == viewed


@pytest.mark.django_db
@pytest.mark.parametrize(
    'use_movie',
    (True, False))
class TestAjaxDownloadButton:
    @pytest.fixture(autouse=True)
    def setUp(self,
              create_user,
              create_tv_media_file,
              create_movie,
              client):
        self.client = client

        self.tv_mf = create_tv_media_file()
        self.movie = create_movie()

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"fileid": self.tv_mf.id}

        self.url = reverse('mediaviewer:ajaxdownloadbutton')

    def test_user_not_authenticated(self, use_movie):
        if use_movie:
            payload = {'movie_id': self.movie.pk}
        else:
            payload = {'mf_id': self.tv_mf.pk}

        resp = self.client.post(self.url, payload)

        assert resp.status_code == 400
        json_data = resp.json()

        assert json_data == {"errmsg": "User not authenticated. Refresh and try again."}

    def test_valid(self, use_movie):
        if use_movie:
            obj = self.movie
            payload = {'movie_id': self.movie.pk}
        else:
            obj = self.tv_mf
            payload = {'mf_id': self.tv_mf.pk}

        self.client.force_login(self.user)
        resp = self.client.post(self.url, payload)

        assert resp.status_code == 200
        json_data = resp.json()

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

        self.tv_mf = create_tv_media_file()

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
        actual = autoplaydownloadlink(self.request, self.tv_mf.id)

        assert expected == actual
        self.mock_downloadtoken_new.assert_called_once_with(self.user, self.tv_mf)
        self.mock_autoplayDownloadLink.assert_called_once_with(
            self.user, self.mock_downloadtoken_new.return_value.guid
        )
        self.mock_redirect.assert_called_once_with(
            self.mock_autoplayDownloadLink.return_value
        )
