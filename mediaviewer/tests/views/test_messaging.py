import mock

from django.test import TestCase
from django.contrib.auth.models import User
from django.http import HttpRequest

from mediaviewer.models.message import Message

from mediaviewer.views.messaging import (submitsitewidemessage,
                                         ajaxclosemessage,
                                         )


class TestSubmitSiteWideMessage(TestCase):
    def setUp(self):
        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.messaging.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.createSitewideMessage_patcher = mock.patch(
                'mediaviewer.views.messaging.Message.createSitewideMessage')
        self.mock_createSiteWideMessage = (
                self.createSitewideMessage_patcher.start())
        self.addCleanup(self.createSitewideMessage_patcher.stop)

        self.render_patcher = mock.patch(
                'mediaviewer.views.messaging.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        self.user = mock.MagicMock(User)
        self.settings = mock.MagicMock()
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {'sitemessage': 'test_site_message',
                             'level': 'Debug'}

    def test_valid(self):
        expected_context = {'active_page': 'submitsitewidemessage'}

        expected = self.mock_render.return_value
        actual = submitsitewidemessage(self.request)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_createSiteWideMessage.assert_called_once_with(
                'test_site_message',
                level=Message.levelDict['Debug'])
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settingsresults.html',
                expected_context)

    def test_user_not_staff(self):
        self.user.is_staff = False

        expected_context = {'active_page': 'submitsitewidemessage'}

        self.assertRaises(Exception,
                          submitsitewidemessage,
                          self.request)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.assertFalse(self.mock_createSiteWideMessage.called)
        self.assertFalse(self.mock_render.called)

    def test_force_password_change(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = submitsitewidemessage(self.request)
        self.assertEqual(expected, actual)

        self.mock_change_password.assert_called_once_with(self.request)


class TestAjaxCloseMessage(TestCase):
    def setUp(self):
        self.HttpResponse_patcher = mock.patch(
                'mediaviewer.views.messaging.HttpResponse')
        self.mock_HttpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch(
                'mediaviewer.views.messaging.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.filter_patcher = mock.patch(
                'mediaviewer.views.messaging.Message.objects.filter')
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.messageObj = mock.MagicMock(Message)
        self.messageObj.sent = False

        self.mock_filter.return_value = [self.messageObj]

        self.user = mock.MagicMock(User)
        self.user.is_authenticated.return_value = True

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {'messageid': '123'}

    def test_valid(self):
        expected = self.mock_HttpResponse.return_value
        actual = ajaxclosemessage(self.request)

        self.assertEqual(expected, actual)

        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                content_type='application/javascript')
        self.mock_dumps.assert_called_once_with(
                {'errmsg': ''})
        self.assertTrue(self.messageObj.sent)
        self.messageObj.save.assert_called_once_with()

    def test_user_not_authenticated(self):
        self.user.is_authenticated.return_value = False

        expected = self.mock_HttpResponse.return_value
        actual = ajaxclosemessage(self.request)

        self.assertEqual(expected, actual)

        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                content_type='application/javascript')
        self.mock_dumps.assert_called_once_with({
            'errmsg': 'User not authenticated. Refresh and try again.'})
        self.assertFalse(self.messageObj.sent)
        self.assertFalse(self.messageObj.save.called)
