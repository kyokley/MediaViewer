import mock

from django.contrib.auth.models import User
from django.test import TestCase

from mediaviewer.views.requests import addrequests

class TestAddRequests(TestCase):
    def setUp(self):
        self.HttpResponseRedirect_patcher = mock.patch('mediaviewer.views.requests.HttpResponseRedirect')
        self.mock_httpResponseRedirect = self.HttpResponseRedirect_patcher.start()
        self.addCleanup(self.HttpResponseRedirect_patcher.stop)

        self.reverse_patcher = mock.patch('mediaviewer.views.requests.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        settings = mock.MagicMock()
        settings.force_password_change = False
        self.test_user.settings = lambda : settings

        self.request = mock.MagicMock()
        self.request.POST = {'newrequest': 'new request'}
        self.request.user = self.test_user

    def test_(self):
        expected = self.mock_httpResponseRedirect.return_value
        actual = addrequests(self.request)

        self.mock_reverse.assert_called_once_with('mediaviewer:requests')
        self.mock_httpResponseRedirect.assert_called_once_with(self.mock_reverse.return_value)
        self.assertEqual(expected, actual)
