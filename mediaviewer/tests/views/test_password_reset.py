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
        self.PasswordResetConfirmView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordResetConfirmView')
        self.mock_PasswordResetConfirmView = (
                self.PasswordResetConfirmView_patcher.start())
        self.addCleanup(self.PasswordResetConfirmView_patcher.stop)

        self.reverse_patcher = mock.patch(
                'mediaviewer.views.password_reset.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = (
            self.mock_PasswordResetConfirmView
            .return_value.as_view.return_value)
        actual = reset_confirm(
                self.request,
                uidb64='test_uidb64',
                token='test_token')

        self.assertEqual(expected, actual)
        self.mock_PasswordResetConfirmView.assert_called_once_with(
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

        self.PasswordResetView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordResetView')
        self.mock_PasswordResetView = self.PasswordResetView_patcher.start()
        self.addCleanup(self.PasswordResetView_patcher.stop)

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

        expected = (
            self.mock_PasswordResetView.return_value.as_view.return_value)
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_PasswordResetView.assert_called_once_with(
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

        expected = (
            self.mock_PasswordResetView.return_value.as_view.return_value)
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_PasswordResetView.assert_called_once_with(
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

        expected = (
            self.mock_PasswordResetView.return_value.as_view.return_value)
        actual = reset(self.request)

        self.assertEqual(expected, actual)
        self.mock_PasswordResetView.assert_called_once_with(
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
        self.PasswordResetDoneView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordResetDoneView')
        self.mock_PasswordResetDoneView = (
                self.PasswordResetDoneView_patcher.start())
        self.addCleanup(self.PasswordResetDoneView_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = (
            self.mock_PasswordResetDoneView
            .return_value.as_view.return_value)
        actual = reset_done(self.request)

        self.assertEqual(expected, actual)
        self.mock_PasswordResetDoneView.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_done.html')


class TestRestComplete(TestCase):
    def setUp(self):
        self.PasswordResetCompleteView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordResetCompleteView')
        self.mock_PasswordResetCompleteView = (
                self.PasswordResetCompleteView_patcher.start())
        self.addCleanup(self.PasswordResetCompleteView_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = (
            self.mock_PasswordResetCompleteView
            .return_value.as_view.return_value)
        actual = reset_complete(self.request)

        self.assertEqual(expected, actual)
        self.mock_PasswordResetCompleteView.assert_called_once_with(
                self.request,
                template_name='mediaviewer/password_reset_complete.html'
                )


class TestCreateNewPassword(TestCase):
    def setUp(self):
        self.PasswordResetConfirmView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordResetConfirmView')
        self.mock_PasswordResetConfirmView = (
                self.PasswordResetConfirmView_patcher.start())
        self.addCleanup(self.PasswordResetConfirmView_patcher.stop)

        self.reverse_patcher = mock.patch(
                'mediaviewer.views.password_reset.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected = (
            self.mock_PasswordResetConfirmView
            .return_value.as_view.return_value)
        actual = create_new_password(self.request,
                                     uidb64='test_uidb64',
                                     token='test_token'
                                     )

        self.assertEqual(expected, actual)
        self.mock_PasswordResetConfirmView.assert_called_once_with(
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
        self.PasswordChangeView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordChangeView')
        self.mock_PasswordChangeView = self.PasswordChangeView_patcher.start()
        self.addCleanup(self.PasswordChangeView_patcher.stop)

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

        expected = (
            self.mock_PasswordChangeView.return_value.as_view.return_value)
        actual = change_password(self.request)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_reverse.assert_called_once_with(
                'mediaviewer:change_password_submit')
        self.mock_PasswordChangeView.assert_called_once_with(
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

        self.PasswordChangeDoneView_patcher = mock.patch(
                'mediaviewer.views.password_reset.PasswordChangeDoneView')
        self.mock_PasswordChangeDoneView = (
                self.PasswordChangeDoneView_patcher.start())
        self.addCleanup(self.PasswordChangeDoneView_patcher.stop)

        self.request = mock.MagicMock(HttpRequest)

    def test_valid(self):
        expected_context = {'active_page': 'change_password_submit'}

        expected = (
            self.mock_PasswordChangeDoneView.return_value.as_view.return_value)
        actual = change_password_submit(self.request)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_PasswordChangeDoneView.assert_called_once_with(
                self.request,
                template_name='mediaviewer/change_password_submit.html',
                extra_context=expected_context,
                )
