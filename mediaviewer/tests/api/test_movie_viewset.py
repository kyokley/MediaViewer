import pytest
from django.urls import reverse

from mediaviewer.models import Movie, Genre, Poster


@pytest.fixture
def create_movie_genre(genre_name="Action"):
    """Creates a Genre and links it to a movie via Poster."""

    def _create_movie_genre(genre_name=genre_name, movie=None):
        genre = Genre.objects.create(genre=genre_name)
        if movie:
            poster = Poster.objects.from_ref_obj(movie, genres=[genre])
            movie._poster = poster
            movie.save()
        return genre, genre_name

    return _create_movie_genre


@pytest.mark.django_db
@pytest.mark.parametrize("is_staff", (True, False))
class TestMovies:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_movie, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")

        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)

        self.movies = [create_movie() for i in range(3)]

    def test_detail(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        for movie in self.movies:
            url = reverse("mediaviewer:api:movie-detail", args=[movie.pk])
            response = self.client.get(url)
            assert response.status_code == 200

            json_data = response.json()
            assert movie.name == json_data["name"]
            assert movie.pk == json_data["pk"]
            assert (
                dict(path=str(movie.media_path.path), pk=movie.media_path.pk)
                == json_data["media_path"]
            )
            assert movie.finished == json_data["finished"]

    def test_list(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:movie-list")
        response = self.client.get(url)
        assert response.status_code == 200

        json_data = response.json()
        expected = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.movies[0].pk,
                    "name": self.movies[0].name,
                    "media_path": dict(
                        path=str(self.movies[0].media_path.path),
                        pk=self.movies[0].media_path.pk,
                    ),
                    "finished": self.movies[0].finished,
                },
                {
                    "pk": self.movies[1].pk,
                    "name": self.movies[1].name,
                    "media_path": dict(
                        path=str(self.movies[1].media_path.path),
                        pk=self.movies[1].media_path.pk,
                    ),
                    "finished": self.movies[1].finished,
                },
                {
                    "pk": self.movies[2].pk,
                    "name": self.movies[2].name,
                    "media_path": dict(
                        path=str(self.movies[2].media_path.path),
                        pk=self.movies[2].media_path.pk,
                    ),
                    "finished": self.movies[2].finished,
                },
            ],
        }
        assert expected == json_data

    @pytest.mark.parametrize("include_name", (True, False))
    def test_create_new(self, is_staff, include_name):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:movie-list")

        post_data = {"media_path": "/path/to/dir"}

        if include_name:
            post_data["name"] = "test_name"

        response = self.client.post(url, data=post_data)

        if is_staff:
            json_data = response.json()

            assert Movie.objects.count() == 4

            new_movie = Movie.objects.get(pk=json_data["pk"])
            if include_name:
                assert new_movie.name == "test_name"
            else:
                assert new_movie.name == "dir"

            assert str(new_movie.media_path.path) == "/path/to/dir"
            assert not new_movie.finished
        else:
            assert response.status_code == 403
            assert Movie.objects.count() == 3

    def test_create_existing(self, is_staff, create_movie):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        new_movie = create_movie()

        url = reverse("mediaviewer:api:movie-list")

        post_data = {
            "name": new_movie.name,
            "media_path": str(new_movie.media_path.path),
        }

        response = self.client.post(url, data=post_data)

        assert Movie.objects.count() == 4
        if is_staff:
            json_data = response.json()

            assert new_movie.pk == json_data["pk"]
            assert new_movie.name == json_data["name"]
            assert (
                dict(path=str(new_movie.media_path.path), pk=new_movie.media_path.pk)
                == json_data["media_path"]
            )
            assert new_movie.finished == json_data["finished"]
        else:
            assert response.status_code == 403


@pytest.mark.django_db
class TestMCPMovies:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_movie, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.movies = [create_movie(name=f"Movie {i}") for i in range(3)]

    def test_list_requires_filter(self):
        """MCP movie list requires at least one filter parameter."""
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-movie-list")
        response = self.client.get(url)
        assert response.status_code == 400

    def test_list_filter_by_name(self):
        """MCP movie list filters by name (case-insensitive contains)."""
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-movie-list")
        response = self.client.get(url, {"name": self.movies[0].name})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.movies[0].pk in pks
        assert self.movies[1].pk not in pks

    def test_list_filter_by_imdb(self):
        """MCP movie list filters by imdb."""
        poster = Poster.objects.from_ref_obj(self.movies[0], imdb="tt1234567")
        self.movies[0]._poster = poster
        self.movies[0].save()

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-movie-list")
        response = self.client.get(url, {"imdb": "tt1234567"})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.movies[0].pk in pks

    def test_list_filter_by_tmdb(self):
        """MCP movie list filters by tmdb."""
        poster = Poster.objects.from_ref_obj(self.movies[0], tmdb="12345")
        self.movies[0]._poster = poster
        self.movies[0].save()

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-movie-list")
        response = self.client.get(url, {"tmdb": "12345"})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.movies[0].pk in pks

    def test_hidden_movies_excluded(self):
        """MCP movie list excludes hidden movies."""
        Movie.objects.filter(pk=self.movies[0].pk).update(hide=True)

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-movie-list")
        response = self.client.get(url, {"name": self.movies[0].name})
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data) == 0

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read MCP movie list."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:mcp-movie-list")
        response = self.client.get(url, {"name": self.movies[0].name})
        assert response.status_code == 200
