import pytest
from django.urls import reverse
from mediaviewer.models import Movie


@pytest.mark.django_db
@pytest.mark.parametrize('is_staff',
                         (True, False))
class TestMovies:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_movie, create_user):
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
            assert str(movie.media_path.path) == json_data['media_path']
            assert movie.finished == json_data['finished']

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
                {"pk": self.movies[0].pk,
                 "name": self.movies[0].name,
                 'media_path': str(self.movies[0].media_path.path),
                 'finished': self.movies[0].finished,
                 },
                {"pk": self.movies[1].pk,
                 "name": self.movies[1].name,
                 'media_path': str(self.movies[1].media_path.path),
                 'finished': self.movies[1].finished,
                 },
                {"pk": self.movies[2].pk,
                 "name": self.movies[2].name,
                 'media_path': str(self.movies[2].media_path.path),
                 'finished': self.movies[2].finished,
                 },
            ],
        }
        assert expected == json_data

    @pytest.mark.parametrize(
        'include_name',
        (True, False))
    def test_create_new(self, is_staff, include_name):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:movie-list")

        post_data = {'media_path': '/path/to/dir'}

        if include_name:
            post_data['name'] = 'test_name'

        response = self.client.post(url, data=post_data)

        if is_staff:
            json_data = response.json()

            assert Movie.objects.count() == 4

            new_movie = Movie.objects.get(pk=json_data['pk'])
            if include_name:
                assert new_movie.name == 'test_name'
            else:
                assert new_movie.name == '/path/to/dir'

            assert str(new_movie.media_path.path) == '/path/to/dir'
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

        post_data = {'name': new_movie.name,
                     'media_path': str(new_movie.media_path.path)}

        response = self.client.post(url, data=post_data)

        assert Movie.objects.count() == 4
        if is_staff:
            json_data = response.json()

            assert new_movie.pk == json_data['pk']
            assert new_movie.name == json_data['name']
            assert str(new_movie.media_path.path) == json_data['media_path']
            assert new_movie.finished == json_data['finished']
        else:
            assert response.status_code == 403
