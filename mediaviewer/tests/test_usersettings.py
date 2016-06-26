from django.test import TestCase
from mediaviewer.models.usersettings import UserSettings, FormlessPasswordReset
import mock

@mock.patch('mediaviewer.models.usersettings.FormlessPasswordReset')
class TestNewUser(TestCase):
    def setUp(self):
        self.name = 'New User'
        self.email = 'test@user.com'

    def test_new(self, mock_form):
        mock_fake_form_instance = mock.create_autospec(FormlessPasswordReset)
        mock_form.return_value = mock_fake_form_instance
        new_user = UserSettings.new(self.name,
                                    self.email)
        self.assertEqual(new_user.username, self.name)
        self.assertEqual(new_user.email, self.email)
        mock_fake_form_instance.save.assert_called_once_with(email_template_name='mediaviewer/password_create_email.html',
                                                             subject_template_name='mediaviewer/password_create_subject.txt')
