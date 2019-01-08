from django.test import TestCase
from django import forms
from django.contrib.auth.models import User
from mediaviewer.forms import FormlessPasswordReset
import mock


class TestFormlessPasswordReset(TestCase):
    def setUp(self):
        self.is_email_unique_patcher = mock.patch(
            'mediaviewer.forms._is_email_unique')
        self.mock_is_email_unique = self.is_email_unique_patcher.start()
        self.addCleanup(self.is_email_unique_patcher.stop)

        self.email = 'test@email.com'
        self.user = mock.create_autospec(User)

        self.form = FormlessPasswordReset(self.user, self.email)

    def test_save(self):
        self.mock_is_email_unique.return_value = True
        self.form.save()
        self.assertEqual(self.user.email, self.email)
        self.assertTrue(self.user.save.called)

    def test_duplicate_email(self):
        self.mock_is_email_unique.return_value = False

        with self.assertRaises(forms.ValidationError):
            self.form.clean_email()

    def test_unique_email(self):
        self.mock_is_email_unique.return_value = True
        self.form.clean_email()
        self.assertTrue(self.mock_is_email_unique.called)
