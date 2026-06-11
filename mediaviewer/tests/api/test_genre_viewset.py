import pytest
from django.urls import reverse

from mediaviewer.models.genre import Genre


@pytest.mark.django_db
class TestGenreViewSet:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_user):
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)

    def test_list(self):
        Genre.objects.create(genre="Action")
        Genre.objects.create(genre="Comedy")
        Genre.objects.create(genre="Drama")

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:genre-list")
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["count"] == 3
        genres = [item["genre"] for item in json_data["results"]]
        assert "Action" in genres
        assert "Comedy" in genres
        assert "Drama" in genres

    def test_list_ordered_by_genre(self):
        Genre.objects.create(genre="Zombie")
        Genre.objects.create(genre="Action")

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:genre-list")
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        genre_names = [item["genre"] for item in json_data["results"]]
        assert genre_names == sorted(genre_names)

    def test_list_empty(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:genre-list")
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["count"] == 0

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read (safe method)."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:genre-list")
        response = self.client.get(url)
        assert response.status_code == 200
