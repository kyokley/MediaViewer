import pytest
import random
from django.urls import reverse


@pytest.mark.django_db
class TestCollection:
    @pytest.fixture(autouse=True)
    def setUp(
        self,
        client,
        create_user,
        create_collection,
    ):
        self.client = client
        self.user = create_user()

        self.collections = [create_collection() for i in range(5)]

    def test_detail(self):
        collection = random.choice(self.collections)
        self.client.force_login(self.user)

        url = reverse("mediaviewer:api:collection-detail", args=[collection.pk])
        resp = self.client.get(url)
        assert resp.status_code == 200

        json_data = resp.json()
        assert json_data["name"] == collection.name

    def test_list(self):
        expected = {
            "count": len(self.collections),
            "next": None,
            "previous": None,
            "results": [{"name": f"{x.name}", "pk": x.pk} for x in self.collections],
        }

        self.client.force_login(self.user)

        url = reverse("mediaviewer:api:collection-list")
        resp = self.client.get(url)
        assert resp.status_code == 200

        json_data = resp.json()
        assert json_data == expected
