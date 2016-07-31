import mock
from django.test import TestCase
from django.contrib.auth.models import User
#from django.test.client import RequestFactory
from django.http import HttpRequest
from mediaviewer.views.settings import submitnewuser
from mediaviewer.models.usersettings import UserSettings

@mock.patch('mediaviewer.views.settings.UserSettings.new')
@mock.patch('mediaviewer.views.settings.log')
@mock.patch('mediaviewer.views.settings.render')
@mock.patch('mediaviewer.views.settings.setSiteWideContext')
@mock.patch('mediaviewer.views.settings.generateHeader')
class TestNewUserView(TestCase):
    def setUp(self):
        self.user = mock.create_autospec(User)
        self.user.username = 'test_logged_in_user'
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.new_user_email = 'test_new_user@user.com'

        self.request = HttpRequest()
        self.request.user = self.user
        self.request.POST = {'new_user_email': self.new_user_email}

    def test_newUserWithNonStaffer(self,
                                   mock_generateHeader,
                                   mock_setSiteWideContext,
                                   mock_render,
                                   mock_log,
                                   mock_new,
                                   ):
        self.user.is_staff = False
        expected_context = {'successful': False,
                            'header': 'header',
                            'errMsg': 'Unauthorized access attempted'}
        mock_generateHeader.return_value = 'header'
        submitnewuser(self.request)
        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
        mock_log.error.assert_called_once_with("User is not a staffer!")
        self.assertFalse(mock_new.called)

    def test_newUserWithStaffer(self,
                                   mock_generateHeader,
                                   mock_setSiteWideContext,
                                   mock_render,
                                   mock_log,
                                   mock_new,
                                   ):
        self.user.is_staff = True
        expected_context = {'successful': True,
                            'header': 'header',
                            }
        mock_generateHeader.return_value = 'header'
        submitnewuser(self.request)
        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
        self.assertFalse(mock_log.error.called)
        mock_new.assert_called_once_with(self.new_user_email,
                                         self.new_user_email,
                                         can_download=True)
