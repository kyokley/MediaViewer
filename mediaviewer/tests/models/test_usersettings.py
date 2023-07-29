import mock
import pytest

from django.http import HttpRequest
from django.db.utils import IntegrityError
from mediaviewer.models.usersettings import (
    UserSettings,
    case_insensitive_authenticate,
)
from mediaviewer.tests import helpers


@pytest.mark.django_db
@mock.patch("mediaviewer.forms.PasswordResetForm")
class TestNewUser:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.name = " New User "
        self.expected_name = "new user"
        self.email = " test@user.com "

        self.existing_user = " Existing User "
        self.expected_existing_user = "existing user"
        self.existing_email = "existing@user.com"

        helpers.create_user(username=self.existing_user, email=self.existing_email)

    def test_new(self, mock_form):
        new_user = UserSettings.new(self.name, self.email, send_email=False)
        assert new_user.username == self.expected_name

    def test_existing_username(self, mock_form):
        test_username = self.existing_user

        with pytest.raises(IntegrityError):
            UserSettings.new(test_username, self.email, send_email=False)

    def test_existing_username_mixed_case(self, mock_form):
        test_username = "exIsTiNg USeR"

        with pytest.raises(IntegrityError):
            UserSettings.new(test_username, self.email, send_email=False)

    def test_existing_email(self, mock_form):
        with pytest.raises(IntegrityError):
            UserSettings.new(self.name, self.existing_email, send_email=False)

    def test_existing_email_mixed_case(self, mock_form):
        test_email = "ExIsTiNg@uSeR.CoM"

        with pytest.raises(IntegrityError):
            UserSettings.new(self.name, test_email, send_email=False)


@pytest.mark.django_db
class TestCaseInsensitiveAuthenticate:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.name = "New User"
        self.email = "test@user.com"
        self.password = "password"

        self.request = HttpRequest()

        self.new_user = helpers.create_user(username=self.name, email=self.email)
        self.new_user.set_password(self.password)
        self.new_user.save()

        settings = self.new_user.settings()
        settings.allow_password_logins = True
        settings.save()

    def test_password_logins_not_allowed(self):
        settings = self.new_user.settings()
        settings.allow_password_logins = False
        settings.save()

        test_username = self.name
        test_password = self.password
        expected = None
        actual = case_insensitive_authenticate(
            self.request, test_username, test_password
        )

        assert expected == actual

    def test_invalid_user(self):
        test_username = "blah"
        test_password = self.password
        expected = None
        actual = case_insensitive_authenticate(
            self.request, test_username, test_password
        )

        assert expected == actual

    def test_valid_user(self):
        test_username = self.name
        test_password = self.password
        expected = self.new_user
        actual = case_insensitive_authenticate(
            self.request, test_username, test_password
        )

        assert expected == actual

    def test_valid_mixed_case_username(self):
        test_username = "NeW UsEr"
        test_password = self.password
        expected = self.new_user
        actual = case_insensitive_authenticate(
            self.request, test_username, test_password
        )

        assert expected == actual

    def test_incorrect_password(self):
        test_username = self.name
        test_password = "wrong password"
        expected = None
        actual = case_insensitive_authenticate(
            self.request, test_username, test_password
        )

        assert expected == actual
