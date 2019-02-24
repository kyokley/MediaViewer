from django.test import TestCase
from django.contrib.auth.models import User
from mediaviewer.forms import FormlessPasswordReset
import mock


class TestFormlessPasswordReset(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.user = mock.create_autospec(User)

        self.form = FormlessPasswordReset(self.user, self.email)

    def test_save(self):
        self.form.save()
        self.assertEqual(self.user.email, self.email)
        self.assertTrue(self.user.save.called)
