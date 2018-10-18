import mock

from django.test import TestCase
from django.contrib.auth.models import User
from django.http import HttpRequest
from mediaviewer.views.settings import (submitnewuser,
                                        settings,
                                        submitsettings,
                                        submitsitesettings,
                                        )
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.sitegreeting import SiteGreeting
from django.core.exceptions import ValidationError


# TODO: Drop mock patch decorators
@mock.patch('mediaviewer.views.settings.UserSettings.new')
@mock.patch('mediaviewer.views.settings.log')
@mock.patch('mediaviewer.views.settings.render')
@mock.patch('mediaviewer.views.settings.setSiteWideContext')
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
                                   mock_setSiteWideContext,
                                   mock_render,
                                   mock_log,
                                   mock_new,
                                   ):
        self.user.is_staff = False
        expected_context = {'successful': False,
                            'active_page': 'submitnewuser',
                            'errMsg': 'Unauthorized access attempted'}
        submitnewuser(self.request)
        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
        mock_log.error.assert_called_once_with("User is not a staffer!")
        self.assertFalse(mock_new.called)

    def test_newUserWithStaffer(self,
                                mock_setSiteWideContext,
                                mock_render,
                                mock_log,
                                mock_new,
                                ):
        self.user.is_staff = True
        expected_context = {'successful': True,
                            'active_page': 'submitnewuser',
                            }
        submitnewuser(self.request)
        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
        self.assertFalse(mock_log.error.called)
        mock_new.assert_called_once_with(self.new_user_email,
                                         self.new_user_email,
                                         can_download=True)

    def test_newUserRaisesValidationError(self,
                                          mock_setSiteWideContext,
                                          mock_render,
                                          mock_log,
                                          mock_new,
                                          ):
        self.user.is_staff = True
        expected_context = {'successful': False,
                            'active_page': 'submitnewuser',
                            'errMsg': 'This is an error message',
                            }
        mock_new.side_effect = ValidationError('This is an error message')
        submitnewuser(self.request)

        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
        self.assertFalse(mock_log.error.called)
        mock_new.assert_called_once_with(self.new_user_email,
                                         self.new_user_email,
                                         can_download=True)

    def test_newUserRaisesException(self,
                                    mock_setSiteWideContext,
                                    mock_render,
                                    mock_log,
                                    mock_new,
                                    ):
        self.user.is_staff = True
        expected_context = {'successful': False,
                            'active_page': 'submitnewuser',
                            'errMsg': 'This is an error message',
                            }
        mock_new.side_effect = Exception('This is an error message')
        submitnewuser(self.request)

        mock_render.assert_called_once_with(self.request,
                                            'mediaviewer/settingsresults.html',
                                            expected_context)
        self.assertFalse(mock_log.error.called)
        mock_new.assert_called_once_with(self.new_user_email,
                                         self.new_user_email,
                                         can_download=True)


class TestSettings(TestCase):
    def setUp(self):
        self.LOCAL_IP_patcher = mock.patch(
                'mediaviewer.views.settings.LOCAL_IP', 'test_local_ip')
        self.LOCAL_IP_patcher.start()
        self.addCleanup(self.LOCAL_IP_patcher.stop)

        self.BANGUP_IP_patcher = mock.patch(
                'mediaviewer.views.settings.BANGUP_IP', 'test_bangup_ip')
        self.BANGUP_IP_patcher.start()
        self.addCleanup(self.BANGUP_IP_patcher.stop)

        self.latestSiteGreeting_patcher = mock.patch(
                'mediaviewer.views.settings.SiteGreeting.latestSiteGreeting')
        self.mock_latestSiteGreeting = self.latestSiteGreeting_patcher.start()
        self.addCleanup(self.latestSiteGreeting_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.settings.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.settings.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        self.user = mock.create_autospec(User)
        self.user.username = 'test_logged_in_user'
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.new_user_email = 'test_new_user@user.com'

        self.siteGreeting = mock.MagicMock(SiteGreeting)
        self.siteGreeting.greeting = 'test_greeting'
        self.siteGreeting.user = self.user

        self.mock_latestSiteGreeting.return_value = self.siteGreeting

        self.request = HttpRequest()
        self.request.user = self.user

    def test_user_has_email(self):
        expected_context = {
              'LOCAL_IP': 'test_local_ip',
              'BANGUP_IP': 'test_bangup_ip',
              'greeting': 'test_greeting',
              'active_page': 'settings',
              'title': 'Settings',
              'ip_format': self.settings.ip_format,
              'binge_mode': self.settings.binge_mode,
              'jump_to_last': self.settings.jump_to_last_watched,
              'email': self.user.email,
              'display_missing_email_modal': False,
            }
        expected = self.mock_render.return_value
        actual = settings(self.request)
        self.assertEqual(expected, actual)

        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=False)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settings.html',
                expected_context)

        self.assertFalse(self.mock_change_password.called)

    def test_user_has_no_email(self):
        self.user.email = None

        expected_context = {
              'LOCAL_IP': 'test_local_ip',
              'BANGUP_IP': 'test_bangup_ip',
              'greeting': 'test_greeting',
              'active_page': 'settings',
              'title': 'Settings',
              'ip_format': self.settings.ip_format,
              'binge_mode': self.settings.binge_mode,
              'jump_to_last': self.settings.jump_to_last_watched,
              'email': self.user.email,
              'display_missing_email_modal': True,
            }
        expected = self.mock_render.return_value
        actual = settings(self.request)
        self.assertEqual(expected, actual)

        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=False)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settings.html',
                expected_context)

        self.assertFalse(self.mock_change_password.called)

    def test_force_password_change(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = settings(self.request)
        self.assertEqual(expected, actual)

        self.mock_change_password.assert_called_once_with(self.request)


class TestSubmitSettings(TestCase):
    def setUp(self):
        self.FILENAME_SORT_patcher = mock.patch(
                'mediaviewer.views.settings.FILENAME_SORT',
                'test_filename_sort')
        self.FILENAME_SORT_patcher.start()
        self.addCleanup(self.FILENAME_SORT_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.settings.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.settings.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        self.user = mock.create_autospec(User)
        self.user.username = 'test_logged_in_user'
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {}

    def test_defaults(self):
        expected_context = {'successful': True,
                            'active_page': 'submitsettings',
                            'default_sort': 'test_filename_sort',
                            }

        expected = self.mock_render.return_value
        actual = submitsettings(self.request)
        self.assertEqual(expected, actual)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settingsresults.html',
                expected_context)

        self.assertEqual(self.settings.default_sort, 'test_filename_sort')
        self.assertEqual(self.settings.binge_mode, False)
        self.assertEqual(self.settings.jump_to_last_watched, False)

        self.assertFalse(self.mock_change_password.called)

    def test_non_defaults(self):
        self.request.POST = {'default_sort': 'test_default_sort',
                             'binge_mode': 'true',
                             'jump_to_last': 'true',
                             'email_field': 'test_new_email',
                             }

        expected_context = {'successful': True,
                            'active_page': 'submitsettings',
                            'default_sort': 'test_default_sort',
                            }

        expected = self.mock_render.return_value
        actual = submitsettings(self.request)
        self.assertEqual(expected, actual)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settingsresults.html',
                expected_context)

        self.assertEqual(self.settings.default_sort, 'test_default_sort')
        self.assertEqual(self.settings.binge_mode, True)
        self.assertEqual(self.settings.jump_to_last_watched, True)
        self.assertEqual(self.user.email, 'test_new_email')

        self.assertFalse(self.mock_change_password.called)

    def test_force_password_change(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = settings(self.request)
        self.assertEqual(expected, actual)

        self.mock_change_password.assert_called_once_with(self.request)


class TestSubmitSiteSettings(TestCase):
    def setUp(self):
        self.SiteGreeting_patcher = mock.patch(
                'mediaviewer.views.settings.SiteGreeting')
        self.mock_SiteGreeting = self.SiteGreeting_patcher.start()
        self.addCleanup(self.SiteGreeting_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.settings.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.render_patcher = mock.patch('mediaviewer.views.settings.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        self.user = mock.create_autospec(User)
        self.user.username = 'test_logged_in_user'
        self.settings = mock.create_autospec(UserSettings)
        self.settings.force_password_change = False
        self.user.settings.return_value = self.settings

        self.newSiteGreeting = mock.MagicMock(SiteGreeting)
        self.newSiteGreeting.greeting = 'test_greeting'
        self.newSiteGreeting.user = self.user

        self.mock_SiteGreeting.return_value = self.newSiteGreeting

        self.latestSiteGreeting = mock.MagicMock(SiteGreeting)
        self.latestSiteGreeting.greeting = 'test_greeting'
        self.latestSiteGreeting.user = self.user

        self.mock_SiteGreeting.return_value = self.latestSiteGreeting
        self.mock_SiteGreeting.latestSiteGreeting.return_value = (
                self.latestSiteGreeting)

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {'greeting': 'new_greeting'}

    def test_new_greeting(self):
        self.user.is_staff = True
        self.mock_SiteGreeting.latestSiteGreeting.return_value = None

        expected_context = {'successful': True,
                            'active_page': 'submitsitesettings',
                            }

        expected = self.mock_render.return_value
        actual = submitsitesettings(self.request)
        self.assertEqual(expected, actual)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settingsresults.html',
                expected_context)
        self.assertEqual(self.mock_SiteGreeting.return_value.greeting,
                         'new_greeting')

    def test_no_greeting_change(self):
        self.user.is_staff = True
        self.request.POST['greeting'] = self.latestSiteGreeting.greeting

        expected_context = {'successful': True,
                            'active_page': 'submitsitesettings',
                            }

        expected = self.mock_render.return_value
        actual = submitsitesettings(self.request)
        self.assertEqual(expected, actual)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settingsresults.html',
                expected_context)
        self.assertFalse(self.mock_SiteGreeting.called)

    def test_is_not_staff(self):
        self.user.is_staff = False
        self.request.POST['greeting'] = self.latestSiteGreeting.greeting

        expected_context = {'successful': False,
                            'active_page': 'submitsitesettings',
                            'errMsg': 'Unauthorized access attempted',
                            }

        expected = self.mock_render.return_value
        actual = submitsitesettings(self.request)
        self.assertEqual(expected, actual)

        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/settingsresults.html',
                expected_context)
        self.assertFalse(self.mock_SiteGreeting.called)

    def test_force_password_change(self):
        self.settings.force_password_change = True

        expected = self.mock_change_password.return_value
        actual = settings(self.request)
        self.assertEqual(expected, actual)

        self.mock_change_password.assert_called_once_with(self.request)
