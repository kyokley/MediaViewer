import pytest
from django.urls import reverse

from mediaviewer.models.tv import TV
from mediaviewer.models.poster import Poster
from mediaviewer.models.genre import Genre


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
            assert json_data["genres"] == []

    def test_list_requires_filter(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")
        response = self.client.get(url)
        # Permission passes for authenticated users (safe method),
        # but the view requires at least one filter param
        assert response.status_code == 400

    def test_list_by_name(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")
        response = self.client.get(url, {"name": self.tv_shows[0].name})
        assert response.status_code == 200
        json_data = response.json()
        # Overridden list returns plain list, not paginated
        assert len(json_data) == 1
        assert json_data[0]["pk"] == self.tv_shows[0].pk

    def test_list_by_imdb(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")
        response = self.client.get(url, {"imdb": "tt1234567"})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == []

    def test_list_by_tmdb(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")
        response = self.client.get(url, {"tmdb": "12345"})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == []

    def test_list_hidden_tv_excluded(self, is_staff, create_tv):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        hidden_tv = create_tv(hide=True)

        url = reverse("mediaviewer:api:tv-list")
        response = self.client.get(url, {"name": hidden_tv.name})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == []

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
class TestTVByIMDB:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.tv_shows = [create_tv() for i in range(3)]

    def test_list_requires_imdb_id(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:tv-imdb-list")
        response = self.client.get(url)
        assert response.status_code == 400
        assert "imdb_id" in str(response.json())

    def test_list_filters_by_imdb_id(self):
        self.client.force_login(self.user)
        tv_with_imdb = self.tv_shows[0]
        Poster.objects.from_ref_obj(tv_with_imdb, imdb="tt1234567")

        url = reverse("mediaviewer:api:tv-imdb-list")
        response = self.client.get(url, {"imdb_id": "tt1234567"})
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) == 1
        assert json_data[0]["pk"] == tv_with_imdb.pk

    def test_list_no_match(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:tv-imdb-list")
        response = self.client.get(url, {"imdb_id": "tt9999999"})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == []

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read (safe method)."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:tv-imdb-list")
        response = self.client.get(url, {"imdb_id": "tt1234567"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestTVByGenre:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.tv_shows = [create_tv() for i in range(3)]

    def test_list_requires_genre(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:tv-genre-list")
        response = self.client.get(url)
        assert response.status_code == 400
        assert "genre" in str(response.json())

    def test_list_by_genre(self):
        genre = Genre.objects.create(genre="Action")
        tv_with_genre = self.tv_shows[0]
        Poster.objects.from_ref_obj(tv_with_genre, genres=[genre])

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:tv-genre-list")
        response = self.client.get(url, {"genre": "Action"})
        assert response.status_code == 200
        json_data = response.json()
        # Overridden list returns a plain list, not paginated
        pks = [item["pk"] for item in json_data]
        assert tv_with_genre.pk in pks
        for tv in self.tv_shows[1:]:
            assert tv.pk not in pks

    def test_list_genre_not_found(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:tv-genre-list")
        response = self.client.get(url, {"genre": "NonExistentGenre"})
        assert response.status_code == 400
        assert "Genre not found" in str(response.json())

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read (safe method)."""
        genre = Genre.objects.create(genre="Action")
        tv_with_genre = self.tv_shows[0]
        Poster.objects.from_ref_obj(tv_with_genre, genres=[genre])

        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:tv-genre-list")
        response = self.client.get(url, {"genre": "Action"})
        assert response.status_code == 200
