import mock
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase

from mediaviewer.models.request import Request
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.views.requests import (
    addrequests,
    ajaxdone,
    ajaxgiveup,
    ajaxvote,
    requests,
)


class TestRequests(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch(
            "mediaviewer.views.requests.Request.objects.filter"
        )
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
            "mediaviewer.views.requests.setSiteWideContext"
        )
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.render_patcher = mock.patch("mediaviewer.views.requests.render")
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.user = mock.MagicMock(User)
        self.settings = mock.MagicMock()
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

        self.test_requestObj = mock.MagicMock(Request)
        self.mock_filter.return_value = [self.test_requestObj]

    def test_valid(self):
        expected_context = {
            "items": [self.test_requestObj],
            "user": self.user,
            "active_page": "requests",
            "title": "Requests",
        }

        expected = self.mock_render.return_value
        actual = requests(self.request)

        self.assertEqual(expected, actual)
        self.mock_filter.assert_called_once_with(done=False)
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/request.html", expected_context
        )


class TestAddRequests(TestCase):
    def setUp(self):
        self.HttpResponseRedirect_patcher = mock.patch(
            "mediaviewer.views.requests.HttpResponseRedirect"
        )
        self.mock_httpResponseRedirect = self.HttpResponseRedirect_patcher.start()
        self.addCleanup(self.HttpResponseRedirect_patcher.stop)

        self.reverse_patcher = mock.patch("mediaviewer.views.requests.reverse")
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.request_new_patcher = mock.patch("mediaviewer.views.requests.Request.new")
        self.mock_request_new = self.request_new_patcher.start()
        self.addCleanup(self.request_new_patcher.stop)

        self.request_vote_new_patcher = mock.patch(
            "mediaviewer.views.requests.RequestVote.new"
        )
        self.mock_request_vote_new = self.request_vote_new_patcher.start()
        self.addCleanup(self.request_vote_new_patcher.stop)

        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )
        self.settings = mock.MagicMock()
        self.settings.force_password_change = False
        self.test_user.settings = lambda: self.settings

        self.request = mock.MagicMock()
        self.request.POST = {"newrequest": "new request"}
        self.request.user = self.test_user

    def test_valid(self):
        expected = self.mock_httpResponseRedirect.return_value
        actual = addrequests(self.request)

        self.assertEqual(expected, actual)
        self.mock_reverse.assert_called_once_with("mediaviewer:requests")
        self.mock_httpResponseRedirect.assert_called_once_with(
            self.mock_reverse.return_value
        )
        self.mock_request_new.assert_called_once_with("new request", self.test_user)
        self.mock_request_vote_new.assert_called_once_with(
            self.mock_request_new.return_value, self.test_user
        )


class TestAjaxVote(TestCase):
    def setUp(self):
        self.HttpResponse_patcher = mock.patch(
            "mediaviewer.views.requests.HttpResponse"
        )
        self.mock_httpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch("mediaviewer.views.requests.json.dumps")
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.get_object_patcher = mock.patch(
            "mediaviewer.views.requests.get_object_or_404"
        )
        self.mock_get_object = self.get_object_patcher.start()
        self.addCleanup(self.get_object_patcher.stop)

        self.new_patcher = mock.patch("mediaviewer.views.requests.RequestVote.new")
        self.mock_new = self.new_patcher.start()
        self.addCleanup(self.new_patcher.stop)

        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )

        self.request = mock.MagicMock()
        self.request.POST = {"requestid": 123}
        self.request.user = self.test_user

        self.mock_requestObj = mock.MagicMock()
        self.mock_get_object.return_value = self.mock_requestObj

    def test_request_exists(self):
        expected = self.mock_httpResponse.return_value
        actual = ajaxvote(self.request)

        self.assertEqual(expected, actual)
        self.mock_new.assert_called_once_with(self.mock_requestObj, self.test_user)
        self.mock_requestObj.numberOfVotes.assert_called_once_with()
        self.mock_dumps.assert_called_once_with(
            {
                "numberOfVotes": self.mock_requestObj.numberOfVotes.return_value,
                "requestid": 123,
            }
        )
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_user_not_authenticated(self):
        self.test_user = mock.MagicMock()
        self.test_user.is_authenticated = False
        self.request.user = self.test_user

        self.assertRaisesMessage(
            Exception,
            "User not authenticated. Refresh and try again.",
            ajaxvote,
            self.request,
        )


# TODO: Add tests for user messages
class TestAjaxDone(TestCase):
    def setUp(self):
        self.HttpResponse_patcher = mock.patch(
            "mediaviewer.views.requests.HttpResponse"
        )
        self.mock_httpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch("mediaviewer.views.requests.json.dumps")
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.get_object_patcher = mock.patch(
            "mediaviewer.views.requests.get_object_or_404"
        )
        self.mock_get_object = self.get_object_patcher.start()
        self.addCleanup(self.get_object_patcher.stop)

        self.user = mock.create_autospec(User)
        self.user.username = "test_logged_in_user"
        self.user.is_authenticated = True
        self.user.is_staff = True
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock()
        self.request.POST = {"requestid": 123}
        self.request.user = self.user

    def test_user_not_authenticated(self):
        self.user.is_authenticated = False

        expected_response = {"errmsg": "User not authenticated. Refresh and try again."}
        expected = self.mock_httpResponse.return_value
        actual = ajaxdone(self.request)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_user_not_staff(self):
        self.user.is_staff = False

        expected_response = {"errmsg": "User is not a staffer"}
        expected = self.mock_httpResponse.return_value
        actual = ajaxdone(self.request)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_valid(self):
        expected_response = {"errmsg": "", "message": "Marked done!", "requestid": 123}
        expected = self.mock_httpResponse.return_value
        actual = ajaxdone(self.request)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )


class TestGiveUp(TestCase):
    def setUp(self):
        self.HttpResponse_patcher = mock.patch(
            "mediaviewer.views.requests.HttpResponse"
        )
        self.mock_httpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch("mediaviewer.views.requests.json.dumps")
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.get_object_patcher = mock.patch(
            "mediaviewer.views.requests.get_object_or_404"
        )
        self.mock_get_object = self.get_object_patcher.start()
        self.addCleanup(self.get_object_patcher.stop)

        self.user = mock.create_autospec(User)
        self.user.username = "test_logged_in_user"
        self.user.is_authenticated = True
        self.user.is_staff = True
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock()
        self.request.POST = {"requestid": 123}
        self.request.user = self.user

    def test_user_not_authenticated(self):
        self.user.is_authenticated = False

        expected_response = {"errmsg": "User not authenticated. Refresh and try again."}
        expected = self.mock_httpResponse.return_value
        actual = ajaxgiveup(self.request)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_user_not_staff(self):
        self.user.is_staff = False

        expected_response = {"errmsg": "User is not a staffer"}
        expected = self.mock_httpResponse.return_value
        actual = ajaxgiveup(self.request)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )

    def test_valid(self):
        expected_response = {"errmsg": "", "message": "Give up!", "requestid": 123}
        expected = self.mock_httpResponse.return_value
        actual = ajaxgiveup(self.request)

        self.assertEqual(expected, actual)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_httpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )
