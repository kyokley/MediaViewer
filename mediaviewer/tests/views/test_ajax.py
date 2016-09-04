from django.test import TestCase
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.views.ajax import ajaxvideoprogress

import mock

@mock.patch('mediaviewer.views.ajax.json')
@mock.patch('mediaviewer.views.ajax.HttpResponse')
class TestAjaxVideoProgress(TestCase):
    def setUp(self):
        patcher = mock.patch('mediaviewer.views.ajax.DownloadToken')
        self.mock_downloadTokenClass = patcher.start()
        self.addCleanup(patcher.stop)
        self.token = mock.create_autospec(DownloadToken)
        self.mock_downloadTokenClass.getByGUID.return_value = self.token
        self.user = mock.MagicMock()
        self.request = mock.MagicMock()
        self.request.method = 'GET'
        self.guid = 'fakefakefake'
        self.filename = 'a_file_name.mp4'

    def test_invalid_token(self, mock_httpresponse, mock_json):
        fake_json_data = 'json_data'
        mock_json.dumps.return_value = fake_json_data
        fake_httpresponse = 'fake_httpresponse'
        mock_httpresponse.return_value = fake_httpresponse

        self.token.isvalid = False
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        mock_httpresponse.assert_called_once_with(fake_json_data,
                                                  content_type='application/json',
                                                  status=412)
        self.assertEquals(ret_val, fake_httpresponse)

    def test_no_user(self, mock_httpresponse, mock_json):
        fake_json_data = 'json_data'
        mock_json.dumps.return_value = fake_json_data
        fake_httpresponse = 'fake_httpresponse'
        mock_httpresponse.return_value = fake_httpresponse

        self.token.isvalid = False
        self.token.user = None
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        mock_httpresponse.assert_called_once_with(fake_json_data,
                                                  content_type='application/json',
                                                  status=412)
        self.assertEquals(ret_val, fake_httpresponse)

    def test_no_token(self, mock_httpresponse, mock_json):
        fake_json_data = 'json_data'
        mock_json.dumps.return_value = fake_json_data
        fake_httpresponse = 'fake_httpresponse'
        mock_httpresponse.return_value = fake_httpresponse

        self.mock_downloadTokenClass.getByGUID.return_value = None
        ret_val = ajaxvideoprogress(self.request,
                                    self.guid,
                                    self.filename)
        mock_httpresponse.assert_called_once_with(fake_json_data,
                                                  content_type='application/json',
                                                  status=412)
        self.assertEquals(ret_val, fake_httpresponse)
