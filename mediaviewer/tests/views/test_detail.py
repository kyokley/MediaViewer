import mock

from django.test import TestCase
from mediaviewer.views.detail import ajaxsuperviewed
from mediaviewer.models.downloadtoken import DownloadToken

class TestAjaxSuperViewed(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch('mediaviewer.views.detail.DownloadToken.objects.filter', autospec=True)
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.HttpResponse_patcher = mock.patch('mediaviewer.views.detail.HttpResponse', autospec=True)
        self.mock_HttpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch('mediaviewer.views.detail.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.token = mock.MagicMock(DownloadToken)
        self.token.isvalid = True

        self.mock_filter.return_value.first.return_value = self.token

        self.request = mock.MagicMock()
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

    def test_no_token(self):
        self.mock_filter.return_value.first.return_value = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': 'Token is invalid',
                                                 'guid': 'test_guid',
                                                 'viewed': True})
        self.mock_HttpResponse.assert_called_once_with(self.mock_dumps.return_value,
                                                       status=400,
                                                       content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.assertFalse(self.token.file.markFileViewed.called)

    def test_token_invalid(self):
        self.token.isvalid = False

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': 'Token is invalid',
                                                 'guid': 'test_guid',
                                                 'viewed': True})
        self.mock_HttpResponse.assert_called_once_with(self.mock_dumps.return_value,
                                                       status=400,
                                                       content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.assertFalse(self.token.file.markFileViewed.called)

    def test_not_viewed(self):
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'False'}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': '',
                                                 'guid': 'test_guid',
                                                 'viewed': False})
        self.mock_HttpResponse.assert_called_once_with(self.mock_dumps.return_value,
                                                       status=200,
                                                       content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.token.file.markFileViewed.assert_called_once_with(self.token.user, False)

    def test_viewed(self):
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': '',
                                                 'guid': 'test_guid',
                                                 'viewed': True})
        self.mock_HttpResponse.assert_called_once_with(self.mock_dumps.return_value,
                                                       status=200,
                                                       content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.token.file.markFileViewed.assert_called_once_with(self.token.user, True)

class TestAjaxSuperViewedFunctional(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch('mediaviewer.views.detail.DownloadToken.objects.filter', autospec=True)
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.dumps_patcher = mock.patch('mediaviewer.views.detail.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.token = mock.MagicMock(DownloadToken)
        self.token.isvalid = True

        self.mock_filter.return_value.first.return_value = self.token

        self.request = mock.MagicMock()
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

    def test_success(self):
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

        resp = ajaxsuperviewed(self.request)
        self.assertEquals(resp.status_code, 200)

    def test_failure(self):
        self.token.isvalid = False
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

        resp = ajaxsuperviewed(self.request)
        self.assertEquals(resp.status_code, 400)
