import mock
import pytz

from django.test import TestCase
from django.http import HttpRequest

from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.genre import Genre

from mediaviewer.views.ajax import ajaxvideoprogress, ajaxgenres

from mediaviewer.tests.helpers import create_user

from datetime import datetime, timedelta


class TestAjaxVideoProgress(TestCase):
    def setUp(self):
        rewind_patcher = mock.patch(
                'mediaviewer.views.ajax.REWIND_THRESHOLD', 10)
        rewind_patcher.start()
        self.addCleanup(rewind_patcher.stop)

        dt_patcher = mock.patch('mediaviewer.views.ajax.DownloadToken')
        self.mock_downloadTokenClass = dt_patcher.start()
        self.addCleanup(dt_patcher.stop)

        json_patcher = mock.patch('mediaviewer.views.ajax.json')
        self.mock_jsonClass = json_patcher.start()
        self.addCleanup(json_patcher.stop)
        self.fake_json_data = 'json_data'
        self.mock_jsonClass.dumps.return_value = self.fake_json_data

        vp_patcher = mock.patch('mediaviewer.views.ajax.VideoProgress')
        self.mock_vpClass = vp_patcher.start()
        self.addCleanup(vp_patcher.stop)
        self.vp = mock.create_autospec(VideoProgress)
        self.date_edited = datetime.now(pytz.timezone('utc'))
        self.vp.offset = 345.123
        self.vp.date_edited = self.date_edited
        self.mock_vpClass.get.return_value = self.vp
        self.mock_vpClass.createOrUpdate.return_value = self.vp

        http_response_patcher = mock.patch(
                'mediaviewer.views.ajax.HttpResponse')
        self.mock_httpResponseClass = http_response_patcher.start()
        self.addCleanup(http_response_patcher.stop)
        self.fake_httpresponse = 'fake_httpresponse'
        self.mock_httpResponseClass.return_value = self.fake_httpresponse

        self.token = mock.create_autospec(DownloadToken)
        self.token.ismovie = False
        self.token.filename = 'dt.filename.mp4'
        self.mock_downloadTokenClass.getByGUID.return_value = self.token
        self.user = mock.MagicMock()
        self.token.user = self.user

        self.request = mock.MagicMock()
        self.request.method = 'GET'
        self.guid = 'fakefakefake'
        self.filename = 'a_file_name.mp4'

    def test_invalid_token(self):
        self.token.isvalid = False
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=412)
        self.mock_jsonClass.dumps.assert_called_once_with({'offset': 0})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_no_user(self):
        self.token.isvalid = False
        self.token.user = None
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=412)
        self.mock_jsonClass.dumps.assert_called_once_with({'offset': 0})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_no_token(self):
        self.mock_downloadTokenClass.getByGUID.return_value = None
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=412)
        self.mock_jsonClass.dumps.assert_called_once_with({'offset': 0})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_get_request_with_movie(self):
        self.request.method = 'GET'
        self.token.ismovie = True
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_vpClass.get.assert_called_once_with(self.user,
                                                      self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=200)
        self.mock_jsonClass.dumps.assert_called_once_with(
                {'offset': 345.123,
                 'date_edited': self.date_edited.isoformat()})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_get_request_no_movie(self):
        self.request.method = 'GET'
        self.token.ismovie = False
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_vpClass.get.assert_called_once_with(self.user,
                                                      self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=200)
        self.mock_jsonClass.dumps.assert_called_once_with(
                {'offset': 345.123,
                 'date_edited': self.date_edited.isoformat()})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_get_request_with_movie_with_rewind(self):
        self.request.method = 'GET'
        self.token.ismovie = True
        self.vp.date_edited = self.vp.date_edited - timedelta(minutes=11)
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_vpClass.get.assert_called_once_with(self.user,
                                                      self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=200)
        self.mock_jsonClass.dumps.assert_called_once_with(
                {'offset': 315.123,
                 'date_edited': self.vp.date_edited.isoformat()})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_get_request_no_movie_with_rewind(self):
        self.request.method = 'GET'
        self.token.ismovie = False
        self.vp.date_edited = self.vp.date_edited - timedelta(minutes=11)
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_vpClass.get.assert_called_once_with(self.user,
                                                      self.filename)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=200)
        self.mock_jsonClass.dumps.assert_called_once_with(
                {'offset': 315.123,
                 'date_edited': self.vp.date_edited.isoformat()})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_post_request_with_movie(self):
        self.request.method = 'POST'
        fake_post_data = {'offset': 987}
        self.request.POST = fake_post_data
        self.token.ismovie = True
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.assertFalse(self.mock_vpClass.get.called)
        self.mock_vpClass.createOrUpdate.assert_called_once_with(
                self.user,
                'dt.filename.mp4',
                self.filename,
                987,
                self.token.file)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=200)
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_post_request_no_movie(self):
        self.request.method = 'POST'
        fake_post_data = {'offset': 987}
        self.request.POST = fake_post_data
        self.token.ismovie = False
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.assertFalse(self.mock_vpClass.get.called)
        self.mock_vpClass.createOrUpdate.assert_called_once_with(
                self.user,
                'dt.filename.mp4',
                self.filename,
                987,
                self.token.file)
        self.mock_httpResponseClass.assert_called_once_with(
                self.fake_json_data,
                content_type='application/json',
                status=200)
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_delete(self):
        self.request.method = 'DELETE'
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.assertFalse(self.mock_vpClass.get.called)
        self.assertFalse(self.mock_vpClass.createOrUpdate.called)
        self.mock_httpResponseClass.assert_called_once_with(
                'json_data', content_type='application/json', status=204)
        self.mock_vpClass.destroy.assert_called_once_with(
                self.user, self.filename)
        self.assertEquals(ret_val, self.fake_httpresponse)


class TestAjaxGenres(TestCase):
    def setUp(self):
        getByGUID_patcher = mock.patch(
                'mediaviewer.views.ajax.DownloadToken.getByGUID')
        self.mock_getByGUID = getByGUID_patcher.start()
        self.addCleanup(getByGUID_patcher.stop)

        get_movie_genres_patcher = mock.patch(
                'mediaviewer.views.ajax.File.get_movie_genres')
        self.mock_get_movie_genres = get_movie_genres_patcher.start()
        self.addCleanup(get_movie_genres_patcher.stop)

        get_tv_genres_patcher = mock.patch(
                'mediaviewer.views.ajax.Path.get_tv_genres')
        self.mock_get_tv_genres = get_tv_genres_patcher.start()
        self.addCleanup(get_tv_genres_patcher.stop)

        dumps_patcher = mock.patch(
                'mediaviewer.views.ajax.json.dumps')
        self.mock_dumps = dumps_patcher.start()
        self.addCleanup(dumps_patcher.stop)

        HttpResponse_patcher = mock.patch(
                'mediaviewer.views.ajax.HttpResponse')
        self.mock_HttpResponse = HttpResponse_patcher.start()
        self.addCleanup(HttpResponse_patcher.stop)

        self.user = create_user()

        self.dt = mock.MagicMock(DownloadToken)
        self.dt.user = self.user
        self.dt.isvalid = True
        self.mock_getByGUID.return_value = self.dt

        self.movie_genre = mock.MagicMock(Genre)
        self.mock_get_movie_genres.return_value = [self.movie_genre]

        self.tv_genre = mock.MagicMock(Genre)
        self.mock_get_tv_genres.return_value = [self.tv_genre]

        self.request = mock.MagicMock(HttpRequest)
        self.request.method = 'GET'
        self.test_guid = 'test_guid'

    def test_no_token(self):
        self.mock_getByGUID.return_value = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        self.assertEqual(expected, actual)
        self.mock_HttpResponse.assert_called_once_with(
                None,
                content_type='application/json',
                status=412)
        self.assertFalse(self.mock_get_movie_genres.called)
        self.assertFalse(self.mock_get_tv_genres.called)
        self.assertFalse(self.mock_dumps.called)

    def test_no_token_user(self):
        self.dt.user = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        self.assertEqual(expected, actual)
        self.mock_HttpResponse.assert_called_once_with(
                None,
                content_type='application/json',
                status=412)
        self.assertFalse(self.mock_get_movie_genres.called)
        self.assertFalse(self.mock_get_tv_genres.called)
        self.assertFalse(self.mock_dumps.called)

    def test_token_not_valid(self):
        self.dt.isvalid = False

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        self.assertEqual(expected, actual)
        self.mock_HttpResponse.assert_called_once_with(
                None,
                content_type='application/json',
                status=412)
        self.assertFalse(self.mock_get_movie_genres.called)
        self.assertFalse(self.mock_get_tv_genres.called)
        self.assertFalse(self.mock_dumps.called)

    def test_valid(self):
        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(
                {'movie_genres': [(self.movie_genre.id,
                                   self.movie_genre.genre)],
                 'tv_genres': [(self.tv_genre.id,
                                self.tv_genre.genre)],
                 })
        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                content_type='application/json',
                status=200)

    def test_bad_method(self):
        self.request.method = 'POST'

        expected = self.mock_HttpResponse.return_value
        actual = ajaxgenres(self.request, self.test_guid)

        self.assertEqual(expected, actual)
        self.mock_HttpResponse.assert_called_once_with(
                None,
                content_type='application/json',
                status=405)
        self.assertFalse(self.mock_get_movie_genres.called)
        self.assertFalse(self.mock_get_tv_genres.called)
        self.assertFalse(self.mock_dumps.called)
