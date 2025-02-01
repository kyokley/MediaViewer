import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestCollection:
    @pytest.fixture(autouse=True)
    def setUp(
        self,
        client,
        create_tv,
        create_movie,
        create_collection,
        create_user,
    ):
        self.user = create_user()

        self.client = client
        self.collection = create_collection()

        self.tv = create_tv()
        self.movie = create_movie()

        self.url = reverse("mediaviewer:collection", kwargs=dict(pk=self.collection.pk))

    def test_smoke(self):
        self.client.force_login(self.user)
        self.client.get(self.url)
