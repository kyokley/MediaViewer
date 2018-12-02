import mock

from django.test import TestCase

from mediaviewer.views.signout import signout


class TestSignout(TestCase):
    def setUp(self):
        self.logout_patcher = mock.patch('mediaviewer.views.signout.logout')
        self.mock_logout = self.logout_patcher.start()
        self.addCleanup(self.logout_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.signout.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.signout.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.request = mock.MagicMock()

    def test_signout(self):
        expected_context = {'active_page': 'logout',
                            'loggedin': False,
                            'title': 'Signed out'}

        expected = self.mock_render.return_value
        actual = signout(self.request)

        self.assertEqual(expected, actual)
        self.mock_logout.assert_called_once_with(self.request)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context, self.request)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/logout.html',
                expected_context)
