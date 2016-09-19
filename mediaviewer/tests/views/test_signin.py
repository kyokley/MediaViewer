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
        self.addCleanup(self.generateHeader_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch('mediaviewer.views.signin.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.case_insensitive_authenticate_patcher = mock.patch('mediaviewer.views.signin.case_insensitive_authenticate')
        self.mock_case_insensitive_authenticate = self.case_insensitive_authenticate_patcher.start()
        self.addCleanup(self.case_insensitive_authenticate_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.signin.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.login_patcher = mock.patch('mediaviewer.views.signin.login')
        self.mock_login = self.login_patcher.start()
        self.addCleanup(self.login_patcher.stop)

        self.LoginEvent_patcher = mock.patch('mediaviewer.views.signin.LoginEvent')
        self.mock_LoginEvent = self.LoginEvent_patcher.start()
        self.addCleanup(self.LoginEvent_patcher.stop)

        self.request = mock.MagicMock()

    def test_request_not_POST(self):
        self.request.GET = {'next': 'next_field'}
        signin(self.request)

        self.assertFalse(self.mock_case_insensitive_authenticate.called)
        self.assertFalse(self.mock_login.called)
        self.assertFalse(self.mock_LoginEvent.new.called)
