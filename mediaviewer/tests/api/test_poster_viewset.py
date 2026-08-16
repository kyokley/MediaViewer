import pytest
from django.urls import reverse

from mediaviewer.models.poster import Poster


@pytest.mark.django_db
class TestPosterViewSet:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.tv = create_tv()

    def test_list_requires_filter(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-list")
        response = self.client.get(url)
        assert response.status_code == 400

    def test_list_filter_by_tv_id(self):
        Poster.objects.from_ref_obj(self.tv)
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-list")
        response = self.client.get(url, {"tv_id": self.tv.pk})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data[0]["tv"] == self.tv.pk

    def test_list_filter_by_imdb(self):
        Poster.objects.from_ref_obj(self.tv, imdb="tt1234567")
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-list")
        response = self.client.get(url, {"imdb": "tt1234567"})
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) >= 1
        assert json_data[0]["imdb"] == "tt1234567"

    def test_list_filter_by_tmdb(self):
        Poster.objects.from_ref_obj(self.tv, tmdb="12345")
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-list")
        response = self.client.get(url, {"tmdb": "12345"})
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) >= 1
        assert json_data[0]["tmdb"] == "12345"

    def test_list_filter_by_episode_name(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-list")
        response = self.client.get(url, {"episode_name": "test"})
        assert response.status_code == 200

    def test_detail(self):
        poster = Poster.objects.from_ref_obj(self.tv)
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-detail", args=[poster.pk])
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["pk"] == poster.pk

    def test_detail_not_found(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-poster-detail", args=[99999])
        response = self.client.get(url)
        assert response.status_code == 404

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read (safe method)."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:mcp-poster-list")
        response = self.client.get(url, {"tv_id": 0})
        assert response.status_code == 200
