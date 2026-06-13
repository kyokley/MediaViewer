import pytest
from django.db import IntegrityError

from mediaviewer.models.apikey import ApiKey


@pytest.mark.django_db
class TestApiKey:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user()

    def test_create(self):
        """ApiKey is created with an auto-generated key."""
        key = ApiKey.objects.create(user=self.user)
        assert key.key is not None
        assert len(key.key) > 0
        assert key.user == self.user

    def test_key_is_unique(self):
        """ApiKey key field is unique."""
        key1 = ApiKey.objects.create(user=self.user)
        with pytest.raises(IntegrityError):
            ApiKey.objects.create(key=key1.key, user=self.user)

    def test_key_auto_generated(self):
        """Each ApiKey gets a unique auto-generated key."""
        key1 = ApiKey.objects.create(user=self.user)
        key2 = ApiKey.objects.create(user=self.user)
        assert key1.key != key2.key

    def test_key_length(self):
        """ApiKey key does not exceed max_length."""
        key = ApiKey.objects.create(user=self.user)
        assert len(key.key) <= 48

    def test_str_representation(self):
        """String representation shows username and truncated key."""
        key = ApiKey.objects.create(user=self.user)
        expected = f"{self.user.username} - ...{key.key[:4]}"
        assert str(key) == expected

    def test_cascade_delete_user(self):
        """ApiKey is deleted when its user is deleted."""
        key = ApiKey.objects.create(user=self.user)
        pk = key.pk
        self.user.delete()
        assert ApiKey.objects.filter(pk=pk).count() == 0
