import pytest
from django.urls import reverse

from mediaviewer.models import Genre, Poster, TV


@pytest.mark.django_db
@pytest.mark.parametrize("is_staff", (True, False))
class TestTv:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")

        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)

        self.tv_shows = [create_tv() for i in range(3)]

    def test_detail(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        for tv in self.tv_shows:
            url = reverse("mediaviewer:api:tv-detail", args=[tv.pk])
            response = self.client.get(url)
            assert response.status_code == 200

            json_data = response.json()
            assert tv.name == json_data["name"]
            assert tv.pk == json_data["pk"]
            assert str(tv.media_path.path) == json_data["media_paths"][0]["path"]
            assert tv.finished == json_data["finished"]

    @pytest.mark.parametrize("include_name", (True, False))
    def test_create_new(self, is_staff, include_name):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")

        post_data = {"media_path": "/path/to/dir"}

        if include_name:
            post_data["name"] = "test_name"

        response = self.client.post(url, data=post_data)

        if is_staff:
            json_data = response.json()

            assert TV.objects.count() == 4

            new_tv_obj = TV.objects.get(pk=json_data["pk"])
            if include_name:
                assert new_tv_obj.name == "test_name"
            else:
                assert new_tv_obj.name == "dir"

            assert str(new_tv_obj.media_path.path) == "/path/to/dir"
            assert not new_tv_obj.finished
        else:
            assert response.status_code == 403
            assert TV.objects.count() == 3

    def test_create_existing(self, is_staff, create_tv):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        new_tv = create_tv()

        url = reverse("mediaviewer:api:tv-list")

        post_data = {"name": new_tv.name, "media_path": str(new_tv.media_path.path)}

        response = self.client.post(url, data=post_data)

        assert TV.objects.count() == 4
        if is_staff:
            json_data = response.json()

            assert new_tv.pk == json_data["pk"]
            assert new_tv.name == json_data["name"]
            assert str(new_tv.media_path.path) == json_data["media_paths"][0]["path"]
            assert new_tv.finished == json_data["finished"]
        else:
            assert response.status_code == 403


@pytest.mark.django_db
class TestMCPTv:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.tv_shows = [create_tv(name=f"TV Show {i}") for i in range(3)]

    def test_list_requires_filter(self):
        """MCP TV list requires at least one filter parameter."""
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url)
        assert response.status_code == 400

    def test_list_filter_by_name(self):
        """MCP TV list filters by name (case-insensitive contains)."""
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"name": self.tv_shows[0].name})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.tv_shows[0].pk in pks
        assert self.tv_shows[1].pk not in pks

    def test_list_filter_by_genre(self):
        """MCP TV list filters by genre through poster."""
        genre = Genre.objects.create(genre="Action")
        poster = Poster.objects.from_ref_obj(self.tv_shows[0], genres=[genre])
        self.tv_shows[0]._poster = poster
        self.tv_shows[0].save()

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"genre": "Action"})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.tv_shows[0].pk in pks
        assert self.tv_shows[1].pk not in pks

    def test_list_filter_by_imdb(self):
        """MCP TV list filters by imdb."""
        poster = Poster.objects.from_ref_obj(self.tv_shows[0], imdb="tt1234567")
        self.tv_shows[0]._poster = poster
        self.tv_shows[0].save()

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"imdb": "tt1234567"})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.tv_shows[0].pk in pks

    def test_list_filter_by_tmdb(self):
        """MCP TV list filters by tmdb."""
        poster = Poster.objects.from_ref_obj(self.tv_shows[0], tmdb="12345")
        self.tv_shows[0]._poster = poster
        self.tv_shows[0].save()

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"tmdb": "12345"})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.tv_shows[0].pk in pks

    def test_serializer_includes_genres(self):
        """MCP TV serializer includes genres from poster."""
        genre1 = Genre.objects.create(genre="Action")
        genre2 = Genre.objects.create(genre="Comedy")
        poster = Poster.objects.from_ref_obj(self.tv_shows[0], genres=[genre1, genre2])
        self.tv_shows[0]._poster = poster
        self.tv_shows[0].save()

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"name": self.tv_shows[0].name})
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) == 1
        assert set(json_data[0]["genres"]) == {"Action", "Comedy"}

    def test_serializer_genres_empty_when_no_poster(self):
        """MCP TV serializer returns empty genres when no poster."""
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"name": self.tv_shows[0].name})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data[0]["genres"] == []

    def test_hidden_tv_excluded(self):
        """MCP TV list excludes hidden TV shows."""
        TV.objects.filter(pk=self.tv_shows[0].pk).update(hide=True)

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"name": self.tv_shows[0].name})
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) == 0

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read MCP TV list."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:mcp-tv-list")
        response = self.client.get(url, {"name": self.tv_shows[0].name})
        assert response.status_code == 200
