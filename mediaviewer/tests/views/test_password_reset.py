import mock

from django.test import TestCase
from django.contrib.auth.models import User
from django.http import HttpRequest

from mediaviewer.models.usersettings import UserSettings
from mediaviewer.forms import (MVSetPasswordForm,
                               PasswordResetFormWithBCC,
                               MVPasswordChangeForm,
                               )

from mediaviewer.views.password_reset import (reset_confirm,
                                              reset,
                                              reset_done,
                                              reset_complete,
                                              create_new_password,
                                              change_password,
                                              change_password_submit,
                                              )


class TestResetConfirm(TestCase):
    def setUp(self):
        self.password_reset_confirm_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_reset_confirm')
        self.mock_password_reset_confirm = (
                self.password_reset_confirm_patcher.start())
        self.addCleanup(self.password_reset_confirm_patcher.stop)

        self.reverse_patcher = mock.patch(
                'mediaviewer.views.password_reset.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = self.mock_password_reset_confirm.return_value
        actual = reset_confirm(
                self.request,
                uidb64='test_uidb64',
                token='test_token')

        self.assertEqual(expected, actual)
        self.mock_password_reset_confirm.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_confirm.html',
                uidb64='test_uidb64',
                token='test_token',
                set_password_form=MVSetPasswordForm,
                post_reset_redirect=self.mock_reverse.return_value,
                )
        self.mock_reverse.assert_called_once_with(
                'mediaviewer:password_reset_complete')


class TestReset(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch(
                'mediaviewer.views.password_reset.User.objects.filter')
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.render_patcher = mock.patch(
                'mediaviewer.views.password_reset.render')
        self.mock_render = self.render_patcher.start()
        self.addCleanup(self.render_patcher.stop)

        self.password_reset_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_reset')
        self.mock_password_reset = self.password_reset_patcher.start()
        self.addCleanup(self.password_reset_patcher.stop)

        self.reverse_patcher = mock.patch(
                'mediaviewer.views.password_reset.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.user = mock.MagicMock(User)
        self.mock_filter.return_value.first.return_value = self.user

        self.request = mock.MagicMock(HttpRequest)

    def test_POST_with_email_no_user(self):
        self.mock_filter.return_value.first.return_value = None

        self.request.method = 'POST'
        self.request.POST = {'email': 'test_email'}

        expected = self.mock_render.return_value
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/password_reset_no_email.html',
                {'email': 'test_email'})
        self.mock_filter.assert_called_once_with(
                email__iexact='test_email')
        self.mock_filter.return_value.first.assert_called_once_with()

    def test_POST_no_email(self):
        self.mock_filter.return_value.first.return_value = None

        self.request.method = 'POST'
        self.request.POST = {'email': ''}

        expected = self.mock_password_reset.return_value
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_password_reset.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_form.html',
                email_template_name='mediaviewer/password_reset_email.html',
                subject_template_name='mediaviewer/password_reset_subject.txt',
                post_reset_redirect=self.mock_reverse.return_value,
                password_reset_form=PasswordResetFormWithBCC,
                )
        self.assertFalse(self.mock_filter.called)

    def test_POST_with_email_and_user(self):
        self.mock_filter.return_value.first.return_value = self.user

        self.request.method = 'POST'
        self.request.POST = {'email': 'test_email'}

        expected = self.mock_password_reset.return_value
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_password_reset.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_form.html',
                email_template_name='mediaviewer/password_reset_email.html',
                subject_template_name='mediaviewer/password_reset_subject.txt',
                post_reset_redirect=self.mock_reverse.return_value,
                password_reset_form=PasswordResetFormWithBCC,
                )
        self.mock_filter.assert_called_once_with(
                email__iexact='test_email')
        self.mock_filter.return_value.first.assert_called_once_with()

    def test_not_POST(self):
        self.request.method = 'GET'

        expected = self.mock_password_reset.return_value
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_password_reset.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_form.html',
                email_template_name='mediaviewer/password_reset_email.html',
                subject_template_name='mediaviewer/password_reset_subject.txt',
                post_reset_redirect=self.mock_reverse.return_value,
                password_reset_form=PasswordResetFormWithBCC,
                )
        self.assertFalse(self.mock_filter.called)


class TestResetDone(TestCase):
    def setUp(self):
        self.password_reset_done_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_reset_done')
        self.mock_password_reset_done = (
                self.password_reset_done_patcher.start())
        self.addCleanup(self.password_reset_done_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = self.mock_password_reset_done.return_value
        actual = reset_done(self.request)

        self.assertEqual(expected, actual)
        self.mock_password_reset_done.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_done.html')


class TestRestComplete(TestCase):
    def setUp(self):
        self.password_reset_complete_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_reset_complete')
        self.mock_password_reset_complete = (
                self.password_reset_complete_patcher.start())
        self.addCleanup(self.password_reset_complete_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = self.mock_password_reset_complete.return_value
        actual = reset_complete(self.request)

        self.assertEqual(expected, actual)
        self.mock_password_reset_complete.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_complete.html'
                )


class TestCreateNewPassword(TestCase):
    def setUp(self):
        self.password_reset_confirm_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_reset_confirm')
        self.mock_password_reset_confirm = (
                self.password_reset_confirm_patcher.start())
        self.addCleanup(self.password_reset_confirm_patcher.stop)

        self.reverse_patcher = mock.patch(
                'mediaviewer.views.password_reset.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = self.mock_password_reset_confirm.return_value
        actual = create_new_password(self.request,
                                     uidb64='test_uidb64',
                                     token='test_token'
                                     )

        self.assertEqual(expected, actual)
        self.mock_password_reset_confirm.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_create_confirm.html',
                uidb64='test_uidb64',
                token='test_token',
                set_password_form=MVSetPasswordForm,
                post_reset_redirect=self.mock_reverse.return_value,
                )
        self.mock_reverse.assert_called_once_with(
                'mediaviewer:password_reset_complete')


class TestChangePassword(TestCase):
    def setUp(self):
        self.password_change_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_change')
        self.mock_password_change = self.password_change_patcher.start()
        self.addCleanup(self.password_change_patcher.stop)

        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.password_reset.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.reverse_patcher = mock.patch(
                'mediaviewer.views.password_reset.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.user = mock.MagicMock(User)
        self.settings = mock.MagicMock(UserSettings)

        self.user.settings.return_value = self.settings

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
                'force_change': self.settings.force_password_change,
                'active_page': 'change_password'
                }

        expected = self.mock_password_change.return_value
        actual = change_password(self.request)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_reverse.assert_called_once_with(
                'mediaviewer:change_password_submit')
        self.mock_password_change.assert_called_once_with(
                self.request,
                template_name='mediaviewer/change_password.html',
                post_change_redirect=self.mock_reverse.return_value,
                password_change_form=MVPasswordChangeForm,
                extra_context=expected_context,
                )


class TestChangePasswordSubmit(TestCase):
    def setUp(self):
        self.setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.password_reset.setSiteWideContext')
        self.mock_setSiteWideContext = self.setSiteWideContext_patcher.start()
        self.addCleanup(self.setSiteWideContext_patcher.stop)

        self.password_change_done_patcher = mock.patch(
                'mediaviewer.views.password_reset.password_change_done')
        self.mock_password_change_done = (
                self.password_change_done_patcher.start())
        self.addCleanup(self.password_change_done_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected_context = {'active_page': 'change_password_submit'}

        expected = self.mock_password_change_done.return_value
        actual = change_password_submit(self.request)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_password_change_done.assert_called_once_with(
                self.request,
                template_name='mediaviewer/change_password_submit.html',
                extra_context=expected_context,
                )
