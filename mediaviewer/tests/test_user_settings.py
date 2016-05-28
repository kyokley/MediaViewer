import mock
from django.test import TestCase

from mediaviewer.models.usersettings import change_user_password, InvalidPasswordException

class TestChangeUserPassword(TestCase):
    def setUp(self):
        self.user = mock.MagicMock()

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
