from django.test import TestCase
from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.forms import (InvalidPasswordException,
                               FormlessPasswordReset,
                               change_user_password,
                               )
import mock

class TestChangeUserPassword(TestCase):
    def setUp(self):
        self.user = mock.MagicMock()
        self.settings = mock.MagicMock()
        self.settings.force_password_change = False

        self.user.settings.return_value = self.settings

    def test_incorrect_old_password_raises(self):
        self.user.check_password.return_value = False

        old_password = 'old pass'
        new_password = 'new pass'
        confirm_password = 'new pass'

        self.assertRaisesMessage(InvalidPasswordException,
                                 'Incorrect password',
                                 change_user_password,
                                 self.user,
                                 old_password,
                                 new_password,
                                 confirm_password)
        self.user.check_password.assert_called_once_with(old_password)
        self.user.set_password.called = False
        self.assertFalse(self.settings.force_password_change)
        self.settings.save.called = False
        self.user.save.called = False

    def test_new_password_mismatch_raises(self):
        self.user.check_password.return_value = True

        old_password = 'old pass'
        new_password = 'new pass'
        confirm_password = 'another pass'

        self.assertRaisesMessage(InvalidPasswordException,
                                 'New passwords do not match',
                                 change_user_password,
                                 self.user,
                                 old_password,
                                 new_password,
                                 confirm_password)
        self.user.check_password.assert_called_once_with(old_password)
        self.user.set_password.called = False
        self.assertFalse(self.settings.force_password_change)
        self.settings.save.called = False
        self.user.save.called = False

    def test_new_matches_old_password_raises(self):
        self.user.check_password.return_value = True

        old_password = 'old pass'
        new_password = 'old pass'
        confirm_password = 'old pass'

        self.assertRaisesMessage(InvalidPasswordException,
                                 'New and old passwords must be different',
                                 change_user_password,
                                 self.user,
                                 old_password,
                                 new_password,
                                 confirm_password)
        self.user.check_password.assert_called_once_with(old_password)
        self.user.set_password.called = False
        self.assertFalse(self.settings.force_password_change)
        self.settings.save.called = False
        self.user.save.called = False

    def test_password_has_no_numbers_raises(self):
        self.user.check_password.return_value = True

        old_password = 'old pass'
        new_password = 'new pass'
        confirm_password = 'new pass'

        self.assertRaisesMessage(InvalidPasswordException,
                                 'Password is too weak. Valid passwords must contain at least one numeric character.',
                                 change_user_password,
                                 self.user,
                                 old_password,
                                 new_password,
                                 confirm_password)
        self.user.check_password.assert_called_once_with(old_password)
        self.user.set_password.called = False
        self.assertFalse(self.settings.force_password_change)
        self.settings.save.called = False
        self.user.save.called = False

    def test_password_has_no_characters_raises(self):
        self.user.check_password.return_value = True

        old_password = 'old pass'
        new_password = '123456'
        confirm_password = '123456'

        self.assertRaisesMessage(InvalidPasswordException,
                                 'Password is too weak. Valid passwords must contain at least one alphabetic character.',
                                 change_user_password,
                                 self.user,
                                 old_password,
                                 new_password,
                                 confirm_password)
        self.user.check_password.assert_called_once_with(old_password)
        self.user.set_password.called = False
        self.assertFalse(self.settings.force_password_change)
        self.settings.save.called = False
        self.user.save.called = False

    def test_password_too_short_raises(self):
        self.user.check_password.return_value = True

        old_password = 'old pass'
        new_password = 'abc12'
        confirm_password = 'abc12'

        self.assertRaisesMessage(InvalidPasswordException,
                                 'Password is too weak. Valid passwords must be at least 6 characters long.',
                                 change_user_password,
                                 self.user,
                                 old_password,
                                 new_password,
                                 confirm_password)
        self.user.check_password.assert_called_once_with(old_password)
        self.user.set_password.called = False
        self.assertFalse(self.settings.force_password_change)
        self.settings.save.called = False
        self.user.save.called = False

    def test_valid_password(self):
        self.user.check_password.return_value = True

        old_password = 'old pass'
        new_password = 'new pass 123'
        confirm_password = 'new pass 123'

        change_user_password(self.user,
                             old_password,
                             new_password,
                             confirm_password)
        self.user.set_password.assert_called_once_with(new_password)
        self.settings.force_password_change = False
        self.settings.save.assert_called_once_with()
        self.user.save.assert_called_once_with()

@mock.patch('mediaviewer.models.usersettings.FormlessPasswordReset')
class TestNewUser(TestCase):
    def setUp(self):
        self.mv_group = Group()
        self.mv_group.name = 'MediaViewer'
        self.mv_group.save()
        self.name = 'New User'
        self.email = 'test@user.com'

    def test_new(self, mock_form):
        mock_fake_form_instance = mock.create_autospec(FormlessPasswordReset)
        mock_form.return_value = mock_fake_form_instance
        new_user = UserSettings.new(self.name,
                                    self.email)
        self.assertEqual(new_user.username, self.name)
        mock_fake_form_instance.save.assert_called_once_with(email_template_name='mediaviewer/password_create_email.html',
                                                             subject_template_name='mediaviewer/password_create_subject.txt')
