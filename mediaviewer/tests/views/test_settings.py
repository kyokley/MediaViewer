import mock
import pytest

from django.contrib.auth.models import User
from django.http import HttpRequest
from mediaviewer.views.settings import (
    submitnewuser,
    settings,
    submitsettings,
    submitsitesettings,
)
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.sitegreeting import SiteGreeting
from django.core.exceptions import ValidationError

from mediaviewer.tests.helpers import create_user


# TODO: Drop mock patch decorators
@mock.patch("mediaviewer.views.settings.UserSettings.new")
@mock.patch("mediaviewer.views.settings.log")
@mock.patch("mediaviewer.views.settings.render")
@mock.patch("mediaviewer.views.settings.setSiteWideContext")
class TestNewUserView:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user = mock.create_autospec(User)
        self.user.username = "test_logged_in_user"
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.new_user_email = "test_new_user@user.com"

        self.request = HttpRequest()
        self.request.user = self.user
        self.request.POST = {"new_user_email": self.new_user_email}

    def test_newUserWithNonStaffer(
        self,
        mock_setSiteWideContext,
        mock_render,
        mock_log,
        mock_new,
    ):
        self.user.is_staff = False
        expected_context = {
            "successful": False,
            "active_page": "submitnewuser",
            "errMsg": "Unauthorized access attempted",
        }
        submitnewuser(self.request)
        mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        mock_log.error.assert_called_once_with("User is not a staffer!")
        assert not mock_new.called

    def test_newUserWithStaffer(
        self,
        mock_setSiteWideContext,
        mock_render,
        mock_log,
        mock_new,
    ):
        self.user.is_staff = True
        expected_context = {
            "successful": True,
            "active_page": "submitnewuser",
        }
        submitnewuser(self.request)
        mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        assert not mock_log.error.called
        mock_new.assert_called_once_with(
            self.new_user_email, self.new_user_email, can_download=True
        )

    def test_newUserRaisesValidationError(
        self,
        mock_setSiteWideContext,
        mock_render,
        mock_log,
        mock_new,
    ):
        self.user.is_staff = True
        expected_context = {
            "successful": False,
            "active_page": "submitnewuser",
            "errMsg": "This is an error message",
        }
        mock_new.side_effect = ValidationError("This is an error message")
        submitnewuser(self.request)

        mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        assert not mock_log.error.called
        mock_new.assert_called_once_with(
            self.new_user_email, self.new_user_email, can_download=True
        )

    def test_newUserRaisesException(
        self,
        mock_setSiteWideContext,
        mock_render,
        mock_log,
        mock_new,
    ):
        self.user.is_staff = True
        expected_context = {
            "successful": False,
            "active_page": "submitnewuser",
            "errMsg": "This is an error message",
        }
        mock_new.side_effect = Exception("This is an error message")
        submitnewuser(self.request)

        mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        assert not mock_log.error.called
        mock_new.assert_called_once_with(
            self.new_user_email, self.new_user_email, can_download=True
        )


class TestSettings:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.LOCAL_IP_patcher = mocker.patch(
            "mediaviewer.views.settings.LOCAL_IP", "test_local_ip"
        )

        self.BANGUP_IP_patcher = mocker.patch(
            "mediaviewer.views.settings.BANGUP_IP", "test_bangup_ip"
        )

        self.mock_latestSiteGreeting = mocker.patch(
            "mediaviewer.views.settings.SiteGreeting.latestSiteGreeting"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.settings.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.settings.render")

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.user = mock.create_autospec(User)
        self.user.username = "test_logged_in_user"
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.new_user_email = "test_new_user@user.com"

        self.siteGreeting = mock.MagicMock(SiteGreeting)
        self.siteGreeting.greeting = "test_greeting"
        self.siteGreeting.user = self.user

        self.mock_latestSiteGreeting.return_value = self.siteGreeting

        self.request = HttpRequest()
        self.request.user = self.user

    def test_user_has_email(self):
        expected_context = {
            "LOCAL_IP": "test_local_ip",
            "BANGUP_IP": "test_bangup_ip",
            "greeting": "test_greeting",
            "active_page": "settings",
            "title": "Settings",
            "ip_format": self.settings.ip_format,
            "binge_mode": self.settings.binge_mode,
            "jump_to_last": self.settings.jump_to_last_watched,
            "email": self.user.email,
            "display_missing_email_modal": False,
        }
        expected = self.mock_render.return_value
        actual = settings(self.request)
        assert expected == actual

        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=False
        )

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settings.html", expected_context
        )

        assert not self.mock_change_password.called

    def test_user_has_no_email(self):
        self.user.email = None

        expected_context = {
            "LOCAL_IP": "test_local_ip",
            "BANGUP_IP": "test_bangup_ip",
            "greeting": "test_greeting",
            "active_page": "settings",
            "title": "Settings",
            "ip_format": self.settings.ip_format,
            "binge_mode": self.settings.binge_mode,
            "jump_to_last": self.settings.jump_to_last_watched,
            "email": self.user.email,
            "display_missing_email_modal": True,
        }
        expected = self.mock_render.return_value
        actual = settings(self.request)
        assert expected == actual

        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=False
        )

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settings.html", expected_context
        )

        assert not self.mock_change_password.called

    def test_force_password_change(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = settings(self.request)
        assert expected == actual

        self.mock_change_password.assert_called_once_with()


class TestSubmitSettings:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        mocker.patch("mediaviewer.views.settings.FILENAME_SORT", "test_filename_sort")

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.settings.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.settings.render")

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.user = mock.create_autospec(User)
        self.user.username = "test_logged_in_user"
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {}

    def test_defaults(self):
        expected_context = {
            "successful": True,
            "active_page": "submitsettings",
            "default_sort": "test_filename_sort",
        }

        expected = self.mock_render.return_value
        actual = submitsettings(self.request)
        assert expected == actual

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )

        assert self.settings.default_sort == "test_filename_sort"
        assert self.settings.binge_mode is False
        assert self.settings.jump_to_last_watched is False

        assert not self.mock_change_password.called

    def test_non_defaults(self):
        self.request.POST = {
            "default_sort": "test_default_sort",
            "binge_mode": "true",
            "jump_to_last": "true",
            "email_field": "test_new_email",
        }

        expected_context = {
            "successful": True,
            "active_page": "submitsettings",
            "default_sort": "test_default_sort",
        }

        expected = self.mock_render.return_value
        actual = submitsettings(self.request)
        assert expected == actual

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )

        assert self.settings.default_sort == "test_default_sort"
        assert self.settings.binge_mode is True
        assert self.settings.jump_to_last_watched is True
        assert self.user.email == "test_new_email"

        assert not self.mock_change_password.called

    def test_force_password_change(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = settings(self.request)
        assert expected == actual

        self.mock_change_password.assert_called_once_with()


@pytest.mark.django_db
class TestSubmitSiteSettings:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_new = mocker.patch("mediaviewer.views.settings.SiteGreeting.new")

        self.mock_latestSiteGreeting = mocker.patch(
            "mediaviewer.views.settings.SiteGreeting.latestSiteGreeting"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.settings.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.settings.render")

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.old_greeting = mock.MagicMock(SiteGreeting)
        self.old_greeting.greeting = "old_greeting"

        self.mock_latestSiteGreeting.return_value = self.old_greeting

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"greeting": "new_greeting"}

    def test_new_greeting(self):
        self.user.is_staff = True

        expected_context = {
            "successful": True,
            "active_page": "submitsitesettings",
        }

        expected = self.mock_render.return_value
        actual = submitsitesettings(self.request)
        assert expected == actual

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        self.mock_new.assert_called_once_with(self.user, "new_greeting")

    def test_no_greeting_change(self):
        self.user.is_staff = True
        self.request.POST["greeting"] = "old_greeting"

        expected_context = {
            "successful": True,
            "active_page": "submitsitesettings",
        }

        expected = self.mock_render.return_value
        actual = submitsitesettings(self.request)
        assert expected == actual

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        assert not self.mock_new.called

    def test_is_not_staff(self):
        self.user.is_staff = False

        expected_context = {
            "successful": False,
            "active_page": "submitsitesettings",
            "errMsg": "Unauthorized access attempted",
        }

        expected = self.mock_render.return_value
        actual = submitsitesettings(self.request)
        assert expected == actual

        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/settingsresults.html", expected_context
        )
        assert not self.mock_new.called

    def test_force_password_change(self):
        user_settings = self.user.settings()
        user_settings.force_password_change = True
        user_settings.save()

        expected = self.mock_change_password.return_value
        actual = submitsitesettings(self.request)
        assert expected == actual

        self.mock_change_password.assert_called_once_with()
