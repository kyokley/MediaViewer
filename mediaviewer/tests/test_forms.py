from django.test import TestCase
from django import forms
from django.contrib.auth.models import User
from mediaviewer.forms import FormlessPasswordReset
import mock

class TestFormlessPasswordReset(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.user = mock.create_autospec(User)

        self.form = FormlessPasswordReset(self.user, self.email)

    @mock.patch('mediaviewer.forms._is_email_unique')
    def test_save(self, mock_is_email_unique):
        mock_is_email_unique.return_value = True
        self.form.save()
        self.assertEqual(self.user.email, self.email)
        self.assertTrue(self.user.save.called)

    @mock.patch('mediaviewer.forms._is_email_unique')
    def test_duplicate_email(self, mock_is_email_unique):
        mock_is_email_unique.return_value = False

        with self.assertRaises(forms.ValidationError):
            self.form.clean_email()

    @mock.patch('mediaviewer.forms._is_email_unique')
    def test_unique_email(self, mock_is_email_unique):
        mock_is_email_unique.return_value = True
        self.form.clean_email()
        self.assertTrue(mock_is_email_unique.called)
