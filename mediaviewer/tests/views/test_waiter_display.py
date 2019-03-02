import mock

from django.test import TestCase
from django.http import Http404

from django.contrib.auth.models import User, AnonymousUser
from mediaviewer.views.waiter_display import waiter_display
from mediaviewer.models.path import Path
from mediaviewer.models.file import File
from mediaviewer.models.usersettings import LOCAL_IP


class TestWaiterDisplay(TestCase):
    def setUp(self):
        self.render_patcher = mock.patch(
                'mediaviewer.views.waiter_display.render')
        self.mock_render = self.render_patcher.start()

        self.DownloadToken_new_patcher = mock.patch(
                'mediaviewer.views.waiter_display.DownloadToken.new')
        self.mock_DownloadToken_new = self.DownloadToken_new_patcher.start()

        self.downloadlink_patcher = mock.patch(
                'mediaviewer.views.waiter_display.File.downloadLink')
        self.mock_downloadlink = self.downloadlink_patcher.start()

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.waiter_display.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()

        self.path = Path.new('local.path', 'remote.path', True)
        self.file = File.new('test.filename', self.path)

        self.request = mock.MagicMock()
        self.user = User.objects.create_superuser('test_user',
                                                  'test@user.com',
                                                  'password')

        self.settings = mock.MagicMock()
        self.settings.force_password_change = False
        self.settings.ip_format = LOCAL_IP
        self.user.settings = lambda: self.settings

        self.request.user = self.user

    def tearDown(self):
        self.render_patcher.stop()
        self.DownloadToken_new_patcher.stop()
        self.downloadlink_patcher.stop()
        self.setSiteWideContext_patcher.stop()
        self.change_password_patcher.stop()

    def test_user_authenticated(self):
        expected = self.mock_render.return_value
        actual = waiter_display(self.request, self.file.id)

        expected_context = {
                'active_page': 'home',
                'title': 'Home',
                'guid': self.mock_DownloadToken_new.return_value.guid,
                'isMovie': self.mock_DownloadToken_new.return_value.ismovie,
                'downloadLink': self.mock_downloadlink.return_value,
                'errmsg': '',
                }

        self.assertEqual(expected, actual)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/waiter_display.html',
                expected_context)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=False)

    def test_user_not_authenticated(self):
        self.request.user = AnonymousUser()

        expected = self.mock_render.return_value
        actual = waiter_display(self.request, self.file.id)

        expected_context = {
                'active_page': 'home',
                'title': 'Home',
                'errmsg': 'User not authenticated. Refresh and try again.',
                }

        self.assertEqual(expected, actual)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/waiter_display.html',
                expected_context)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=False)

    def test_no_file(self):
        self.assertRaises(Http404,
                          waiter_display,
                          self.request,
                          0)

    def test_force_change_password(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = waiter_display(self.request, self.file.id)

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with()
