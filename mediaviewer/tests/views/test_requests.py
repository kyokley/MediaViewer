import mock

from django.contrib.auth.models import User
from django.test import TestCase

from mediaviewer.views.requests import addrequests, ajaxvote

class TestAddRequests(TestCase):
    def setUp(self):
        self.HttpResponseRedirect_patcher = mock.patch('mediaviewer.views.requests.HttpResponseRedirect')
        self.mock_httpResponseRedirect = self.HttpResponseRedirect_patcher.start()
        self.addCleanup(self.HttpResponseRedirect_patcher.stop)

        self.reverse_patcher = mock.patch('mediaviewer.views.requests.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.request_new_patcher = mock.patch('mediaviewer.views.requests.Request.new')
        self.mock_request_new = self.request_new_patcher.start()
        self.addCleanup(self.request_new_patcher.stop)

        self.request_vote_new_patcher = mock.patch('mediaviewer.views.requests.RequestVote.new')
        self.mock_request_vote_new = self.request_vote_new_patcher.start()
        self.addCleanup(self.request_vote_new_patcher.stop)

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

        self.assertEqual(expected, actual)
        self.mock_reverse.assert_called_once_with('mediaviewer:requests')
        self.mock_httpResponseRedirect.assert_called_once_with(self.mock_reverse.return_value)
        self.mock_request_new.assert_called_once_with('new request',
                                                      self.test_user)
        self.mock_request_vote_new.assert_called_once_with(self.mock_request_new.return_value,
                                                           self.test_user)

class TestAjaxVote(TestCase):
    def setUp(self):
        self.HttpResponse_patcher = mock.patch('mediaviewer.views.requests.HttpResponse')
        self.mock_httpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch('mediaviewer.views.requests.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.get_object_patcher = mock.patch('mediaviewer.views.requests.get_object_or_404')
        self.mock_get_object = self.get_object_patcher.start()
        self.addCleanup(self.get_object_patcher.stop)

        self.new_patcher = mock.patch('mediaviewer.views.requests.RequestVote.new')
        self.mock_new = self.new_patcher.start()
        self.addCleanup(self.new_patcher.stop)

        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')

        self.request = mock.MagicMock()
        self.request.POST = {'requestid': 123}
        self.request.user = self.test_user

        self.mock_requestObj = mock.MagicMock()
        self.mock_get_object.return_value = self.mock_requestObj

    def test_request_exists(self):
        expected = self.mock_httpResponse.return_value
        actual = ajaxvote(self.request)

        self.assertEqual(expected, actual)
        self.mock_new.assert_called_once_with(self.mock_requestObj,
                                              self.test_user)
        self.mock_requestObj.numberOfVotes.assert_called_once_with()
        self.mock_dumps.assert_called_once_with({'numberOfVotes': self.mock_requestObj.numberOfVotes.return_value,
                                                 'requestid': 123})
        self.mock_httpResponse.assert_called_once_with(self.mock_dumps.return_value,
                                                       content_type='application/javascript')

    def test_user_not_authenticated(self):
        self.test_user = mock.MagicMock()
        self.test_user.is_authenticated.return_value = False
        self.request.user = self.test_user

        self.assertRaisesMessage(Exception,
                                 'User not authenticated. Refresh and try again.',
                                 ajaxvote,
                                 self.request)
