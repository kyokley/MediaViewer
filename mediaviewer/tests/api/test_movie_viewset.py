import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestMovies:
    @pytest.fixture(autouse=True)
    def setUp(self, create_movie, create_user):
        self.user = create_user(is_staff=True)

        self.movies = [create_movie() for i in range(3)]

    def test_detail(self, client):
        client.force_login(self.user)

        for movie in self.movies:
            url = reverse("mediaviewer:api:movie-detail", args=[movie.pk])
            response = client.get(url)
            assert response.status_code == 200

            json_data = response.json()
            assert movie.name == json_data["name"]
            assert movie.pk == json_data["pk"]

    def test_list(self, client):
        client.force_login(self.user)

        url = reverse("mediaviewer:api:movie-list")
        response = client.get(url)
        assert response.status_code == 200

        json_data = response.json()
        expected = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {"pk": self.movies[0].pk, "name": self.movies[0].name},
                {"pk": self.movies[1].pk, "name": self.movies[1].name},
                {"pk": self.movies[2].pk, "name": self.movies[2].name},
            ],
        }
        assert expected == json_data
