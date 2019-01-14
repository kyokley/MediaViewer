import mock

from requests.exceptions import HTTPError
from django.test import TestCase
from mediaviewer.views.waiterstatus import ajaxwaiterstatus


class TestAjaxWaiterStatus(TestCase):
    def setUp(self):
        self.requests_patcher = mock.patch(
            'mediaviewer.views.waiterstatus.requests')
        self.mock_requests = self.requests_patcher.start()
        self.addCleanup(self.requests_patcher.stop)

        settings_patcher = mock.patch(
            'mediaviewer.views.waiterstatus.settings')
        self.mock_settings = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

        self.mock_settings.WAITER_STATUS_URL = 'test_url'
        self.mock_settings.REQUEST_TIMEOUT = 'test_request_timeout'

        self.dumps_patcher = mock.patch(
            'mediaviewer.views.waiterstatus.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.HttpResponse_patcher = mock.patch(
            'mediaviewer.views.waiterstatus.HttpResponse')
        self.mock_HttpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.new_patcher = mock.patch(
            'mediaviewer.views.waiterstatus.WaiterStatus.new')
        self.mock_new = self.new_patcher.start()
        self.addCleanup(self.new_patcher.stop)

        self.mock_resp = mock.MagicMock()
        self.mock_requests.get.return_value = self.mock_resp

        self.mock_request = mock.MagicMock()

    def test_no_status(self):
        self.mock_resp.json.return_value = {}

        actual = ajaxwaiterstatus(self.mock_request)
        expected = self.mock_HttpResponse.return_value

        self.assertEqual(expected, actual)
        self.mock_requests.get.assert_called_once_with(
            'test_url',
            timeout='test_request_timeout')
        self.mock_dumps.assert_called_once_with(
            {'status': False,
             'failureReason': 'Bad Symlink'})
        self.mock_new.assert_called_once_with(False,
                                              'Bad Symlink')
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value,
            content_type='application/javascript')

    def test_bad_status(self):
        self.mock_resp.json.return_value = {'status': False}

        actual = ajaxwaiterstatus(self.mock_request)
        expected = self.mock_HttpResponse.return_value

        self.assertEqual(expected, actual)
        self.mock_requests.get.assert_called_once_with(
            'test_url',
            timeout='test_request_timeout')
        self.mock_dumps.assert_called_once_with(
            {'status': False,
             'failureReason': 'Bad Symlink'})
        self.mock_new.assert_called_once_with(False,
                                              'Bad Symlink')
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value,
            content_type='application/javascript')

    def test_good_status(self):
        self.mock_resp.json.return_value = {'status': True}

        actual = ajaxwaiterstatus(self.mock_request)
        expected = self.mock_HttpResponse.return_value

        self.assertEqual(expected, actual)
        self.mock_requests.get.assert_called_once_with(
            'test_url',
            timeout='test_request_timeout')
        self.mock_dumps.assert_called_once_with({'status': True,
                                                 'failureReason': ''})
        self.mock_new.assert_called_once_with(True,
                                              '')
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value,
            content_type='application/javascript')

    def test_request_timed_out(self):
        self.mock_requests.get.side_effect = HTTPError('Timedout')
        self.mock_resp.json.return_value = {}

        actual = ajaxwaiterstatus(self.mock_request)
        expected = self.mock_HttpResponse.return_value

        self.assertEqual(expected, actual)
        self.mock_requests.get.assert_called_once_with(
            'test_url',
            timeout='test_request_timeout')
        self.mock_dumps.assert_called_once_with({'status': False,
                                                 'failureReason': 'Timedout'})
        self.mock_new.assert_called_once_with(False,
                                              'Timedout')
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value,
            content_type='application/javascript')
