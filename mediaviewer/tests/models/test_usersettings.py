import mock
import pytest
from django.db.utils import IntegrityError
from django.http import HttpRequest
from django.contrib.auth.models import Group

from mediaviewer.models.usersettings import UserSettings, case_insensitive_authenticate
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

    def test_valid_user_with_disallow_password_logins(self):
        test_username = self.name
        test_password = self.password

        settings = self.new_user.settings()
        settings.allow_password_logins = False
        settings.save()

        expected = None
        actual = case_insensitive_authenticate(
            self.request, test_username, test_password
        )

        assert expected == actual


@pytest.mark.django_db
class TestMCPUser:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name="MediaViewer")

    def test_create_mcp_user_creates_api_key(self):
        """Creating a user with is_mcp=True also creates an ApiKey."""
        user = UserSettings.new(
            "mcp_user",
            "mcp@test.com",
            send_email=False,
            is_mcp=True,
            group=self.group,
        )
        assert user.apikey_set.count() == 1
        api_key = user.apikey_set.first()
        assert api_key.key is not None

    def test_non_mcp_user_does_not_get_api_key(self):
        """Creating a user without is_mcp does not create an ApiKey."""
        user = UserSettings.new(
            "regular_user",
            "regular@test.com",
            send_email=False,
            is_mcp=False,
            group=self.group,
        )
        assert user.apikey_set.count() == 0

    def test_create_mcp_user_defaults(self):
        """MCP user is created with correct default fields."""
        user = UserSettings.new(
            "mcp_user2",
            "mcp2@test.com",
            send_email=False,
            is_mcp=True,
            group=self.group,
        )
        assert user.is_staff is False
        assert user.apikey_set.count() == 1
