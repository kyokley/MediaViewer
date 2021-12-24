import pytest
from django.contrib.auth.models import User
from mediaviewer.forms import FormlessPasswordReset
import mock


@pytest.mark.django_db
class TestFormlessPasswordReset:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.email = "test@email.com"
        self.user = mock.create_autospec(User)

        self.form = FormlessPasswordReset(self.user, self.email)

    def test_save(self):
        self.form.save()
        assert self.user.email == self.email
        assert self.user.save.called
