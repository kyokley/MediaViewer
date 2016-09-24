import mock
from django.test import TestCase

from mediaviewer.views.signin import signin

class TestSignin(TestCase):
    def setUp(self):
        self.siteGreeting_patcher = mock.patch('mediaviewer.views.signin.SiteGreeting')
        self.mock_siteGreeting = self.siteGreeting_patcher.start()
        self.mock_greeting = mock.MagicMock()
        self.mock_greeting.greeting = 'latest_site_greeting'
        self.mock_siteGreeting.latestSiteGreeting.return_value = self.mock_greeting
        self.addCleanup(self.siteGreeting_patcher.stop)

        self.generateHeader_patcher = mock.patch('mediaviewer.views.signin.generateHeader')
        self.mock_generateHeader = self.generateHeader_patcher.start()
        self.mock_generateHeader.return_value = 'fake_header'
        self.addCleanup(self.generateHeader_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch('mediaviewer.views.signin.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.case_insensitive_authenticate_patcher = mock.patch('mediaviewer.views.signin.case_insensitive_authenticate')
        self.mock_case_insensitive_authenticate = self.case_insensitive_authenticate_patcher.start()
        self.addCleanup(self.case_insensitive_authenticate_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.signin.render')
        self.mock_render = self.render_patcher.start()
        self.mock_render_return = mock.MagicMock()
        self.mock_render.return_value = self.mock_render_return
        self.addCleanup(self.render_patcher.stop)

        self.login_patcher = mock.patch('mediaviewer.views.signin.login')
        self.mock_login = self.login_patcher.start()
        self.addCleanup(self.login_patcher.stop)

        self.LoginEvent_patcher = mock.patch('mediaviewer.views.signin.LoginEvent')
        self.mock_LoginEvent = self.LoginEvent_patcher.start()
        self.addCleanup(self.LoginEvent_patcher.stop)

        self.request = mock.MagicMock()
        self.user = mock.MagicMock()
        self.settings = mock.MagicMock()
        self.user.settings.return_value = self.settings
        self.request.user = self.user

    def test_request_not_POST(self):
        expected_context = {'loggedin': False,
                            'header': 'fake_header',
                            'greeting': 'latest_site_greeting',
                            'next': 'next_field'}
        self.request.method = 'GET'
        self.request.GET = {'next': 'next_field'}
        ret_val = signin(self.request)

        self.mock_generateHeader.assert_called_once_with('signin', self.request)
        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.assertFalse(self.mock_case_insensitive_authenticate.called)
        self.assertFalse(self.mock_login.called)
        self.assertFalse(self.mock_LoginEvent.new.called)
        self.assertFalse(self.user.settings.called)
        self.mock_render.assert_called_once_with(self.request,
                                                 'mediaviewer/signin.html',
                                                 expected_context)
        self.assertEqual(ret_val,
                         self.mock_render_return)


    def test_request_POST_valid_user(self):
        expected_context = {'loggedin': True,
                            'header': 'fake_header',
                            'greeting': 'latest_site_greeting',
                            'user': self.user,
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = self.user
        self.settings.can_login = True
        ret_val = signin(self.request)

        self.mock_generateHeader.assert_called_once_with('signin', self.request)
        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.mock_case_insensitive_authenticate.assert_called_once_with(username='a@b.c',
                                                                        password='abc123')
        self.mock_login.assert_called_once_with(self.request,
                                                self.user)
        self.mock_LoginEvent.new.assert_called_once_with(self.user)
        self.assertFalse(self.user.settings.called)
        self.mock_render.assert_called_once_with(self.request,
                                                 'mediaviewer/signin.html',
                                                 expected_context)
        self.assertEqual(ret_val,
                         self.mock_render_return)

    def test_request_POST_invalid_user(self):
        expected_context = {'loggedin': False,
                            'header': 'fake_header',
                            'greeting': 'latest_site_greeting',
                            'error_message': 'Incorrect username or password!',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = None
        self.settings.can_login = True
        ret_val = signin(self.request)

        self.mock_generateHeader.assert_called_once_with('signin', self.request)
        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.mock_case_insensitive_authenticate.assert_called_once_with(username='a@b.c',
                                                                        password='abc123')
        self.assertFalse(self.mock_login.called)
        self.assertFalse(self.mock_LoginEvent.new.called)
        self.assertFalse(self.user.settings.called)
        self.mock_render.assert_called_once_with(self.request,
                                                 'mediaviewer/signin.html',
                                                 expected_context)
        self.assertEqual(ret_val,
                         self.mock_render_return)
