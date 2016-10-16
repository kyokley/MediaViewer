from django.test import TestCase
from django.contrib.auth.models import Group
from django.db.utils import IntegrityError
from django import forms
from mediaviewer.models.usersettings import (UserSettings,
                                             case_insensitive_authenticate,
                                             )
from mediaviewer.forms import (InvalidPasswordException,
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

@mock.patch('mediaviewer.forms.PasswordResetForm')
class TestNewUser(TestCase):
    def setUp(self):
        self.mv_group = Group()
        self.mv_group.name = 'MediaViewer'
        self.mv_group.save()
        self.name = 'New User'
        self.email = 'test@user.com'
        self.existing_user = 'Existing User'
        self.existing_email =  'existing@user.com'
        UserSettings.new(self.existing_user, self.existing_email)

    def test_new(self, mock_form):
        new_user = UserSettings.new(self.name,
                                    self.email)
        self.assertEqual(new_user.username, self.name)

    def test_existing_username(self, mock_form):
        test_username = self.existing_user

        with self.assertRaises(IntegrityError):
            UserSettings.new(test_username,
                             self.email)

    def test_existing_username_mixed_case(self, mock_form):
        test_username = 'exIsTiNg USeR'

        with self.assertRaises(IntegrityError):
            UserSettings.new(test_username,
                             self.email)

    def test_existing_email(self, mock_form):
        with self.assertRaises(IntegrityError):
            UserSettings.new(self.name,
                             self.existing_email)

    def test_existing_email_mixed_case(self, mock_form):
        test_email = 'ExIsTiNg@uSeR.CoM'

        with self.assertRaises(IntegrityError):
            UserSettings.new(self.name,
                             test_email)


class TestCaseInsensitiveAuthenticate(TestCase):
    def setUp(self):
        self.mv_group = Group()
        self.mv_group.name = 'MediaViewer'
        self.mv_group.save()
        self.name = 'New User'
        self.email = 'test@user.com'
        self.password = 'password'
        self.new_user = UserSettings.new(self.name,
                                         self.email)
        self.new_user.set_password(self.password)
        self.new_user.save()

    def test_invalid_user(self):
        test_username = 'blah'
        test_password = self.password
        expected = None
        actual = case_insensitive_authenticate(test_username, test_password)

        self.assertEqual(expected, actual)

    def test_valid_user(self):
        test_username = self.name
        test_password = self.password
        expected = self.new_user
        actual = case_insensitive_authenticate(test_username, test_password)

        self.assertEqual(expected, actual)

    def test_valid_mixed_case_username(self):
        test_username = 'NeW UsEr'
        test_password = self.password
        expected = self.new_user
        actual = case_insensitive_authenticate(test_username, test_password)

        self.assertEqual(expected, actual)

    def test_incorrect_password(self):
        test_username = self.name
        test_password = 'wrong password'
        expected = None
        actual = case_insensitive_authenticate(test_username, test_password)

        self.assertEqual(expected, actual)
