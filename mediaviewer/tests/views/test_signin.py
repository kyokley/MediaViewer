import mock
from django.test import TestCase
from django.contrib.auth.models import User

from mediaviewer.views.signin import signin


class TestSignin(TestCase):
    def setUp(self):
        self.user_logged_in_patcher = mock.patch(
            'mediaviewer.views.signin.user_logged_in')
        self.mock_user_logged_in = self.user_logged_in_patcher.start()
        self.addCleanup(self.user_logged_in_patcher.stop)

        self.user_login_failed_patcher = mock.patch(
            'mediaviewer.views.signin.user_login_failed')
        self.mock_user_login_failed = self.user_login_failed_patcher.start()
        self.addCleanup(self.user_login_failed_patcher.stop)

        self.siteGreeting_patcher = mock.patch(
                'mediaviewer.views.signin.SiteGreeting')
        self.mock_siteGreeting = self.siteGreeting_patcher.start()
        self.mock_greeting = mock.MagicMock()
        self.mock_greeting.greeting = 'latest_site_greeting'
        self.mock_siteGreeting.latestSiteGreeting.return_value = (
                self.mock_greeting)
        self.addCleanup(self.siteGreeting_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.signin.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.case_insensitive_authenticate_patcher = mock.patch(
                'mediaviewer.views.signin.case_insensitive_authenticate')
        self.mock_case_insensitive_authenticate = (
                self.case_insensitive_authenticate_patcher.start())
        self.addCleanup(self.case_insensitive_authenticate_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.signin.render')
        self.mock_render = self.render_patcher.start()
        self.mock_render_return = mock.MagicMock()
        self.mock_render.return_value = self.mock_render_return
        self.addCleanup(self.render_patcher.stop)

        self.login_patcher = mock.patch('mediaviewer.views.signin.login')
        self.mock_login = self.login_patcher.start()
        self.addCleanup(self.login_patcher.stop)

        self.LoginEvent_patcher = mock.patch(
                'mediaviewer.views.signin.LoginEvent')
        self.mock_LoginEvent = self.LoginEvent_patcher.start()
        self.addCleanup(self.LoginEvent_patcher.stop)

        self.httpResponseRedirect_patcher = mock.patch(
                'mediaviewer.views.signin.HttpResponseRedirect')
        self.mock_httpResponseRedirect = (
                self.httpResponseRedirect_patcher.start())
        self.mock_redirect = mock.MagicMock()
        self.mock_httpResponseRedirect.return_value = self.mock_redirect
        self.addCleanup(self.httpResponseRedirect_patcher.stop)

        self.reverse_patcher = mock.patch('mediaviewer.views.signin.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.mock_reverse_return = mock.MagicMock()
        self.mock_reverse.return_value = self.mock_reverse_return
        self.addCleanup(self.reverse_patcher.stop)

        self.request = mock.MagicMock()
        self.user = mock.MagicMock(User)
        self.user.is_authenticated = False
        self.settings = mock.MagicMock()
        self.user.settings.return_value = self.settings
        self.request.user = self.user

        self.authenticated_user = mock.MagicMock(User)
        self.authenticated_user.is_authenticated = True
        self.authenticated_user.settings.return_value = self.settings

    def test_request_not_POST(self):
        expected_context = {'loggedin': False,
                            'greeting': 'latest_site_greeting',
                            'next': 'next_field',
                            'active_page': 'signin',
                            }
        self.request.method = 'GET'
        self.request.GET = {'next': 'next_field'}
        self.user.is_authenticated = False
        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.assertFalse(self.mock_setSiteWideContext.called)
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
                            'greeting': 'latest_site_greeting',
                            'user': self.user,
                            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = (
            self.authenticated_user)
        self.settings.can_login = True
        self.settings.force_password_change = False
        self.user.email = 'a@b.c'
        self.user.is_authenticated = False

        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.mock_login.assert_called_once_with(self.request,
                                                self.authenticated_user)
        self.mock_LoginEvent.new.assert_called_once_with(self.user)
        self.mock_httpResponseRedirect.assert_called_once_with(
                self.mock_reverse_return)
        self.assertEqual(ret_val,
                         self.mock_redirect)

    def test_request_POST_valid_user_cannot_login(self):
        expected_context = {
            'loggedin': False,
            'greeting': 'latest_site_greeting',
            'error_message': (
                'You should have received an email with a link '
                'to set up your password the first time. '
                'Please follow the instructions in the email.'),
            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = self.user
        self.settings.can_login = False
        self.settings.force_password_change = False
        self.user.email = 'a@b.c'

        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.assertFalse(self.mock_setSiteWideContext.called)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.assertFalse(self.mock_login.called)
        self.assertFalse(self.mock_LoginEvent.new.called)
        self.assertTrue(self.user.settings.called)
        self.mock_render.assert_called_once_with(self.request,
                                                 'mediaviewer/signin.html',
                                                 expected_context)
        self.assertFalse(self.mock_httpResponseRedirect.called)
        self.assertEqual(ret_val,
                         self.mock_render_return)

    def test_request_POST_valid_user_force_password_change(self):
        expected_context = {'loggedin': True,
                            'greeting': 'latest_site_greeting',
                            'user': self.user,
                            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = (
            self.authenticated_user)
        self.settings.can_login = True
        self.settings.force_password_change = True
        self.user.email = 'a@b.c'
        self.user.is_authenticated = False

        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.mock_login.assert_called_once_with(self.request,
                                                self.authenticated_user)
        self.mock_LoginEvent.new.assert_called_once_with(self.user)
        self.mock_httpResponseRedirect.assert_called_once_with(
                self.mock_reverse_return)
        self.mock_reverse.assert_called_once_with('mediaviewer:settings')
        self.assertEqual(ret_val,
                         self.mock_redirect)

    def test_request_POST_valid_user_no_email(self):
        expected_context = {'loggedin': True,
                            'greeting': 'latest_site_greeting',
                            'user': self.user,
                            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = (
            self.authenticated_user)
        self.settings.can_login = True
        self.settings.force_password_change = False
        self.user.email = None
        self.user.is_authenticated = False

        self.authenticated_user.email = None

        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.mock_login.assert_called_once_with(self.request,
                                                self.authenticated_user)
        self.mock_LoginEvent.new.assert_called_once_with(self.user)
        self.mock_httpResponseRedirect.assert_called_once_with(
                self.mock_reverse_return)
        self.mock_reverse.assert_called_once_with('mediaviewer:settings')
        self.assertEqual(ret_val,
                         self.mock_redirect)

    def test_request_POST_valid_user_next_redirect(self):
        expected_context = {'loggedin': True,
                            'greeting': 'latest_site_greeting',
                            'user': self.user,
                            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123',
                             'next': 'next_url'}
        self.mock_case_insensitive_authenticate.return_value = (
            self.authenticated_user)
        self.settings.can_login = True
        self.settings.force_password_change = False
        self.user.email = 'a@b.c'
        self.user.is_authenticated = False

        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(expected_context,
                                                             self.request)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.mock_login.assert_called_once_with(self.request,
                                                self.authenticated_user)
        self.mock_LoginEvent.new.assert_called_once_with(self.user)
        self.mock_httpResponseRedirect.assert_called_once_with('next_url')
        self.assertFalse(self.mock_reverse.called)
        self.assertEqual(ret_val,
                         self.mock_redirect)

    def test_request_POST_valid_user_not_active(self):
        expected_context = {'loggedin': False,
                            'greeting': 'latest_site_greeting',
                            'error_message': 'User is no longer active',
                            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123',
                             }
        self.mock_case_insensitive_authenticate.return_value = (
            self.authenticated_user)
        self.settings.can_login = True
        self.settings.force_password_change = False
        self.user.email = 'a@b.c'
        self.user.is_active = False
        self.user.is_authenticated = False

        self.authenticated_user.is_active = False

        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.assertFalse(self.mock_setSiteWideContext.called)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.assertFalse(self.mock_login.called)
        self.assertFalse(self.mock_LoginEvent.new.called)
        self.assertFalse(self.mock_httpResponseRedirect.called)
        self.mock_render.assert_called_once_with(self.request,
                                                 'mediaviewer/signin.html',
                                                 expected_context)
        self.assertEqual(ret_val,
                         self.mock_render_return)

    def test_request_POST_invalid_user(self):
        self.user.is_authenticated = False
        expected_context = {'loggedin': False,
                            'greeting': 'latest_site_greeting',
                            'error_message': 'Incorrect username or password!',
                            'active_page': 'signin',
                            }
        self.request.method = 'POST'
        self.request.GET = {}
        self.request.POST = {'username': 'a@b.c',
                             'password': 'abc123'}
        self.mock_case_insensitive_authenticate.return_value = None
        self.settings.can_login = True
        ret_val = signin(self.request)

        self.mock_siteGreeting.latestSiteGreeting.assert_called_once_with()
        self.assertFalse(self.mock_setSiteWideContext.called)
        self.mock_case_insensitive_authenticate.assert_called_once_with(
                username='a@b.c',
                password='abc123')
        self.assertFalse(self.mock_login.called)
        self.assertFalse(self.mock_LoginEvent.new.called)
        self.assertFalse(self.user.settings.called)
        self.mock_render.assert_called_once_with(self.request,
                                                 'mediaviewer/signin.html',
                                                 expected_context)
        self.assertEqual(ret_val,
                         self.mock_render_return)
