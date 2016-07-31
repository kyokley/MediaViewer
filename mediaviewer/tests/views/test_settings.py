import mock
from django.test import TestCase
from django.contrib.auth.models import User
#from django.test.client import RequestFactory
from django.http import HttpRequest
from mediaviewer.views.settings import submitnewuser
from mediaviewer.models.usersettings import UserSettings

@mock.patch('mediaviewer.views.settings.render')
@mock.patch('mediaviewer.views.settings.setSiteWideContext')
@mock.patch('mediaviewer.views.settings.generateHeader')
class TestNewUserWithNonStaffer(TestCase):
    def setUp(self):
        self.user = mock.create_autospec(User)
        self.user.username = 'test_regular_user'
        self.user.is_staff = False
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = HttpRequest()
        self.request.user = self.user
        self.request.POST = {'new_user_email': 'test@user.com'}

    def test_newUserWithNonStaffer(self,
                                   mock_generateHeader,
                                   mock_setSiteWideContext,
                                   mock_render,
                                   ):
        expected_context = {'successful': False,
                            'header': 'header',
                            'errMsg': 'Unauthorized access attempted'}
        mock_generateHeader.return_value = 'header'
        submitnewuser(self.request)
        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
