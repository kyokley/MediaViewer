from datetime import datetime, timedelta

import mock
import pytest
import pytz
from django.contrib import messages
from django.http import Http404, HttpRequest
from django.test import TestCase
from django.urls import reverse

from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.genre import Genre
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.tests.helpers import create_user
from mediaviewer.views.ajax import ajaxgenres, ajaxreport, ajaxvideoprogress


@pytest.mark.django_db
class TestAjaxVideoProgress:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        mocker.patch("mediaviewer.views.ajax.REWIND_THRESHOLD", 10)

        self.mock_downloadTokenClass = mocker.patch("mediaviewer.views.ajax.DownloadToken")

        self.mock_jsonClass = mocker.patch("mediaviewer.views.ajax.json")
        self.fake_json_data = "json_data"
        self.mock_jsonClass.dumps.return_value = self.fake_json_data

        self.mock_vpClass = mocker.patch("mediaviewer.views.ajax.VideoProgress")
        self.vp = mock.create_autospec(VideoProgress)
        self.date_edited = datetime.now(pytz.timezone("utc"))
        self.vp.offset = 345.123
        self.vp.date_edited = self.date_edited
        self.mock_vpClass.objects.filter.return_value.first.return_value = self.vp
        self.mock_vpClass.objects.update_or_create.return_value = (self.vp, False)

        self.mock_httpResponseClass = mocker.patch("mediaviewer.views.ajax.HttpResponse")
        self.fake_httpresponse = "fake_httpresponse"
        self.mock_httpResponseClass.return_value = self.fake_httpresponse

        self.token = mock.create_autospec(DownloadToken)
        self.token.ismovie = False
        self.token.filename = "dt.filename.mp4"
        self.mock_downloadTokenClass.objects.get_by_guid.return_value = self.token
        self.user = mock.MagicMock()
        self.token.user = self.user

        self.request = mock.MagicMock()
        self.request.method = "GET"
        self.guid = "fakefakefake"
        self.filename = "a_file_name.mp4"

    def test_invalid_token(self):
        self.token.isvalid = False
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=412
        )
        self.mock_jsonClass.dumps.assert_called_once_with({"offset": 0})
        assert ret_val == self.fake_httpresponse

    def test_no_user(self):
        self.token.isvalid = False
        self.token.user = None
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=412
        )
        self.mock_jsonClass.dumps.assert_called_once_with({"offset": 0})
        assert ret_val == self.fake_httpresponse

    def test_no_token(self):
        self.mock_downloadTokenClass.objects.get_by_guid.return_value = None
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=412
        )
        self.mock_jsonClass.dumps.assert_called_once_with({"offset": 0})
        assert ret_val == self.fake_httpresponse

    def test_get_request_with_movie(self):
        self.request.method = "GET"
        self.token.ismovie = True
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_vpClass.objects.filter.assert_called_once_with(
            user=self.user, hashed_filename=self.filename
        )
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=200
        )
        self.mock_jsonClass.dumps.assert_called_once_with(
            {"offset": 345.123, "date_edited": self.date_edited.isoformat()}
        )
        assert ret_val == self.fake_httpresponse

    def test_get_request_no_movie(self):
        self.request.method = "GET"
        self.token.ismovie = False
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_vpClass.objects.filter.assert_called_once_with(
            user=self.user, hashed_filename=self.filename
        )
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=200
        )
        self.mock_jsonClass.dumps.assert_called_once_with(
            {"offset": 345.123, "date_edited": self.date_edited.isoformat()}
        )
        assert ret_val == self.fake_httpresponse

    def test_get_request_with_movie_with_rewind(self):
        self.request.method = "GET"
        self.token.ismovie = True
        self.vp.date_edited = self.vp.date_edited - timedelta(minutes=11)
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_vpClass.objects.filter.assert_called_once_with(
            user=self.user, hashed_filename=self.filename
        )
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=200
        )
        self.mock_jsonClass.dumps.assert_called_once_with(
            {"offset": 315.123, "date_edited": self.vp.date_edited.isoformat()}
        )
        assert ret_val == self.fake_httpresponse

    def test_get_request_no_movie_with_rewind(self):
        self.request.method = "GET"
        self.token.ismovie = False
        self.vp.date_edited = self.vp.date_edited - timedelta(minutes=11)
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        self.mock_vpClass.objects.filter.assert_called_once_with(
            user=self.user, hashed_filename=self.filename
        )
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=200
        )
        self.mock_jsonClass.dumps.assert_called_once_with(
            {"offset": 315.123, "date_edited": self.vp.date_edited.isoformat()}
        )
        assert ret_val == self.fake_httpresponse

    def test_post_request_with_movie(self):
        self.request.method = "POST"
        fake_post_data = {"offset": 987}
        self.request.POST = fake_post_data
        self.token.ismovie = True
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        assert not self.mock_vpClass.objects.filter.called
        self.mock_vpClass.objects.update_or_create.assert_called_once_with(
            user=self.user,
            hashed_filename=self.filename,
            defaults=dict(
                offset=987, media_file=self.token.media_file, movie=self.token.movie
            ),
        )
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=200
        )
        assert ret_val == self.fake_httpresponse

    def test_post_request_no_movie(self):
        self.request.method = "POST"
        fake_post_data = {"offset": 987}
        self.request.POST = fake_post_data
        self.token.ismovie = False
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        assert not self.mock_vpClass.objects.filter.called
        self.mock_vpClass.objects.update_or_create.assert_called_once_with(
            user=self.user,
            hashed_filename=self.filename,
            defaults=dict(
                offset=987, media_file=self.token.media_file, movie=self.token.movie
            ),
        )
        self.mock_httpResponseClass.assert_called_once_with(
            self.fake_json_data, content_type="application/json", status=200
        )
        assert ret_val == self.fake_httpresponse

    def test_delete(self):
        self.request.method = "DELETE"
        ret_val = ajaxvideoprogress(self.request, self.guid, self.filename)
        assert not self.mock_vpClass.objects.filter.called
        assert not self.mock_vpClass.objects.update_or_create.called
        self.mock_httpResponseClass.assert_called_once_with(
            "json_data", content_type="application/json", status=204
        )
        self.mock_vpClass.objects.destroy.assert_called_once_with(
            self.user, self.filename
        )
        assert ret_val == self.fake_httpresponse


@pytest.mark.django_db
class TestAjaxGenres:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get_by_guid = mocker.patch(
            "mediaviewer.views.ajax.DownloadToken.objects.get_by_guid"
        )

        self.mock_get_movie_genres = mocker.patch(
            "mediaviewer.views.ajax.Genre.objects.get_movie_genres"
        )

        self.mock_get_tv_genres = mocker.patch(
            "mediaviewer.views.ajax.Genre.objects.get_tv_genres"
        )

        self.mock_dumps = mocker.patch("mediaviewer.views.ajax.json.dumps")

        self.mock_HttpResponse = mocker.patch("mediaviewer.views.ajax.HttpResponse")

        self.user = create_user()

        self.dt = mock.MagicMock(DownloadToken)
        self.dt.user = self.user
        self.dt.isvalid = True
        self.mock_get_by_guid.return_value = self.dt

        self.movie_genre = mock.MagicMock(Genre)
        self.mock_get_movie_genres.return_value = [self.movie_genre]

        self.tv_genre = mock.MagicMock(Genre)
        self.mock_get_tv_genres.return_value = [self.tv_genre]

        self.request = mock.MagicMock(HttpRequest)
        self.request.method = "GET"
        self.test_guid = "test_guid"

    def test_no_token(self):
        self.mock_get_by_guid.return_value = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        assert expected == actual
        self.mock_HttpResponse.assert_called_once_with(
            None, content_type="application/json", status=412
        )
        assert not self.mock_get_movie_genres.called
        assert not self.mock_get_tv_genres.called
        assert not self.mock_dumps.called

    def test_no_token_user(self):
        self.dt.user = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        assert expected == actual
        self.mock_HttpResponse.assert_called_once_with(
            None, content_type="application/json", status=412
        )
        assert not self.mock_get_movie_genres.called
        assert not self.mock_get_tv_genres.called
        assert not self.mock_dumps.called

    def test_token_not_valid(self):
        self.dt.isvalid = False

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        assert expected == actual
        self.mock_HttpResponse.assert_called_once_with(
            None, content_type="application/json", status=412
        )
        assert not self.mock_get_movie_genres.called
        assert not self.mock_get_tv_genres.called
        assert not self.mock_dumps.called

    def test_valid(self):
        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        assert expected == actual
        self.mock_dumps.assert_called_once_with(
            {
                "movie_genres": [(self.movie_genre.id, self.movie_genre.genre)],
                "tv_genres": [(self.tv_genre.id, self.tv_genre.genre)],
            }
        )
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/json", status=200
        )

    def test_bad_method(self):
        self.request.method = "POST"

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        assert expected == actual
        self.mock_HttpResponse.assert_called_once_with(
            None, content_type="application/json", status=405
        )
        assert not self.mock_get_movie_genres.called
        assert not self.mock_get_tv_genres.called
        assert not self.mock_dumps.called


@pytest.mark.django_db
class TestAjaxReport404:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"reportid": "file-100"}

    def test_400(self):
        resp = ajaxreport(self.request)
        assert resp.status_code == 400

    @pytest.mark.parametrize("use_movie", (True, False))
    def test_404(self, use_movie):
        if use_movie:
            self.request.POST.update({"movie_id": "-100"})
        else:
            self.request.POST.update({"mf_id": "-100"})

        with pytest.raises(Http404):
            ajaxreport(self.request)


@pytest.mark.django_db
class TestAjaxReport:
    @pytest.fixture(autouse=True)
    def setUp(
        self, mocker, create_user, create_tv, create_tv_media_file, create_movie, client
    ):
        self.mock_createNewMessage = mocker.patch(
            "mediaviewer.views.ajax.Message.createNewMessage"
        )

        self.tv = create_tv()
        self.tv_mf = create_tv_media_file(tv=self.tv, filename="test_filename")

        self.movie = create_movie()

        self.staff_user = create_user(is_staff=True)

        self.user = create_user()
        self.client = client

        self.payload = {"reportid": "file-123"}

        self.url = reverse("mediaviewer:ajaxreport")

    @pytest.mark.parametrize("use_movie", (True, False))
    def test_valid(self, use_movie):
        self.client.force_login(self.user)

        if use_movie:
            obj = self.movie
            self.payload.update({"movie_id": self.movie.pk})
        else:
            obj = self.tv_mf
            self.payload.update({"mf_id": self.tv_mf.pk})

        resp = self.client.post(self.url, data=self.payload)
        assert resp.status_code == 200

        json_data = resp.json()
        assert json_data["reportid"] == obj.pk
        assert json_data["errmsg"] == ""
        self.mock_createNewMessage.assert_called_once_with(
            self.staff_user,
            f"{obj.name} has been reported by {self.user.username}",
            level=messages.WARNING,
        )
