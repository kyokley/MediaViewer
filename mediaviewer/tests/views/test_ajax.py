from django.test import TestCase
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.views.ajax import ajaxvideoprogress

import mock
from datetime import datetime

class TestAjaxVideoProgress(TestCase):
    def setUp(self):
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
        self.date_edited = datetime.now()
        self.vp.offset = 345.123
        self.vp.date_edited = self.date_edited
        self.mock_vpClass.get.return_value = self.vp
        self.mock_vpClass.createOrUpdate.return_value = self.vp

        http_response_patcher = mock.patch('mediaviewer.views.ajax.HttpResponse')
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
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
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
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
                                                            content_type='application/json',
                                                            status=412)
        self.mock_jsonClass.dumps.assert_called_once_with({'offset': 0})
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_no_token(self):
        self.mock_downloadTokenClass.getByGUID.return_value = None
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
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
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
                                                            content_type='application/json',
                                                            status=200)
        self.assertEquals(ret_val, self.fake_httpresponse)

    def test_get_request_no_movie(self):
        self.request.method = 'GET'
        self.token.ismovie = False
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        self.mock_vpClass.get.assert_called_once_with(self.user,
                                                      self.filename)
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
                                                            content_type='application/json',
                                                            status=200)
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
        self.mock_vpClass.createOrUpdate.assert_called_once_with(self.user,
                                                                 'dt.filename.mp4',
                                                                 self.filename,
                                                                 987,
                                                                 self.token.file)
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
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
        self.mock_vpClass.createOrUpdate.assert_called_once_with(self.user,
                                                                 'dt.filename.mp4',
                                                                 self.filename,
                                                                 987,
                                                                 self.token.file)
        self.mock_httpResponseClass.assert_called_once_with(self.fake_json_data,
                                                            content_type='application/json',
                                                            status=200)
        self.assertEquals(ret_val, self.fake_httpresponse)
