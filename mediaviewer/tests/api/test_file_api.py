import pytest

from django.urls import reverse
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from mediaviewer.models.path import Path
from mediaviewer.models.file import File
from mediaviewer.models.usersettings import UserSettings
from django.test import override_settings


@override_settings(AXES_ENABLED=False)
class MovieFileViewSetTests(APITestCase):
    def setUp(self):
        self.tvPath = Path()
        self.tvPath.localpathstr = "/some/local/path"
        self.tvPath.remotepathstr = "/some/local/path"
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = "a.server"
        self.tvPath.save()

        self.anotherTvPath = Path()
        self.anotherTvPath.localpathstr = "/path/to/folder"
        self.anotherTvPath.remotepathstr = "/path/to/folder"
        self.anotherTvPath.skip = False
        self.anotherTvPath.is_movie = False
        self.anotherTvPath.server = "a.server"
        self.anotherTvPath.save()

        self.tvFile = File()
        self.tvFile.filename = "some.tv.show"
        self.tvFile.skip = False
        self.tvFile.finished = True
        self.tvFile.size = 100
        self.tvFile.streamable = True
        self.tvFile.path = self.tvPath
        self.tvFile.hide = False
        self.tvFile.save()

        self.anotherTvFile = File()
        self.anotherTvFile.filename = "another.tv.show"
        self.anotherTvFile.skip = False
        self.anotherTvFile.finished = True
        self.anotherTvFile.size = 100
        self.anotherTvFile.streamable = True
        self.anotherTvFile.path = self.anotherTvPath
        self.anotherTvFile.hide = False
        self.anotherTvFile.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = "/another/local/path"
        self.moviePath.remotepathstr = "/another/local/path"
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = "a.server"
        self.moviePath.save()

        self.anotherMoviePath = Path()
        self.anotherMoviePath.localpathstr = "/path/to/some/other/movies"
        self.anotherMoviePath.remotepathstr = "/path/to/some/other/movies"
        self.anotherMoviePath.skip = False
        self.anotherMoviePath.is_movie = True
        self.anotherMoviePath.server = "a.server"
        self.anotherMoviePath.save()

        self.movieFile = File()
        self.movieFile.filename = "some.movie.show"
        self.movieFile.skip = False
        self.movieFile.finished = True
        self.movieFile.size = 0
        self.movieFile.streamable = True
        self.movieFile.path = self.moviePath
        self.movieFile.hide = False
        self.movieFile.save()

        self.anotherMovieFile = File()
        self.anotherMovieFile.filename = "another.movie.folder"
        self.anotherMovieFile.skip = False
        self.anotherMovieFile.finished = True
        self.anotherMovieFile.size = 0
        self.anotherMovieFile.streamable = True
        self.anotherMovieFile.path = self.anotherMoviePath
        self.anotherMovieFile.hide = False
        self.anotherMovieFile.save()

        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )
        self.client.login(username="test_user", password="password")

    def test_get_moviefiles_by_pathid(self):
        response = self.client.get(
            reverse("mediaviewer:api:movie-list"), {"pathid": self.moviePath.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.movieFile.id,
                    "path": self.movieFile.path.id,
                    "filename": "some.movie.show",
                    "skip": False,
                    "finished": True,
                    "size": self.movieFile.size,
                    "streamable": True,
                    "localpath": self.movieFile.path.localpathstr,
                    "ismovie": self.movieFile.isMovie(),
                    "displayname": "some movie show",
                    "watched": False,
                }
            ],
        }
        actual = dict(response.data)

        self.assertEqual(expected, actual)

    def test_create_moviefile_using_tvpath(self):
        self.data = {
            "filename": "new file",
            "skip": False,
            "finished": True,
            "size": 100,
            "path": self.tvPath.id,
            "streamable": True,
        }
        response = self.client.post(reverse("mediaviewer:api:movie-list"), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_moviefile_using_moviepath(self):
        self.data = {
            "filename": "new file",
            "skip": False,
            "finished": True,
            "size": 100,
            "path": self.moviePath.id,
            "streamable": True,
        }
        response = self.client.post(reverse("mediaviewer:api:movie-list"), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_valid_moviefile(self):
        self.data = {
            "filename": "new.movie.filename",
            "skip": True,
            "finished": True,
            "size": 0,
            "streamable": True,
        }
        response = self.client.put(
            reverse("mediaviewer:api:movie-detail", args=[self.movieFile.id]), self.data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        movieFile = File.objects.get(pk=response.data["pk"])
        for k, v in self.data.items():
            expected = v
            actual = getattr(movieFile, k)
            self.assertEqual(
                expected,
                actual,
                "attr: %s expected: %s actual: %s" % (k, expected, actual),
            )

    def test_update_invalid_moviefile(self):
        self.data = {
            "filename": "new.movie.filename",
            "skip": True,
            "finished": True,
            "size": 0,
            "streamable": True,
        }
        response = self.client.put(
            reverse("mediaviewer:api:movie-detail", args=[self.tvFile.id]), self.data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(AXES_ENABLED=False)
class TvFileViewSetTests(APITestCase):
    def setUp(self):
        self.tvPath = Path()
        self.tvPath.localpathstr = "/some/local/path"
        self.tvPath.remotepathstr = "/some/local/path"
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = "a.server"
        self.tvPath.save()

        self.anotherTvPath = Path()
        self.anotherTvPath.localpathstr = "/path/to/folder"
        self.anotherTvPath.remotepathstr = "/path/to/folder"
        self.anotherTvPath.skip = False
        self.anotherTvPath.is_movie = False
        self.anotherTvPath.server = "a.server"
        self.anotherTvPath.save()

        self.tvFile = File()
        self.tvFile.filename = "some.tv.show"
        self.tvFile.skip = False
        self.tvFile.finished = True
        self.tvFile.size = 100
        self.tvFile.streamable = True
        self.tvFile.path = self.tvPath
        self.tvFile.hide = False
        self.tvFile.save()

        self.anotherTvFile = File()
        self.anotherTvFile.filename = "another.tv.show"
        self.anotherTvFile.skip = False
        self.anotherTvFile.finished = True
        self.anotherTvFile.size = 100
        self.anotherTvFile.streamable = True
        self.anotherTvFile.path = self.anotherTvPath
        self.anotherTvFile.hide = False
        self.anotherTvFile.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = "/another/local/path"
        self.moviePath.remotepathstr = "/another/local/path"
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = "a.server"
        self.moviePath.save()

        self.movieFile = File()
        self.movieFile.filename = "some.movie.show"
        self.movieFile.skip = False
        self.movieFile.finished = True
        self.movieFile.size = 0
        self.movieFile.streamable = True
        self.movieFile.path = self.moviePath
        self.movieFile.hide = False
        self.movieFile.save()

        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )
        self.client.login(username="test_user", password="password")

    def test_get_tvfiles_by_pathid(self):
        response = self.client.get(
            reverse("mediaviewer:api:tv-list"), {"pathid": self.tvPath.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.tvFile.id,
                    "path": self.tvFile.path.id,
                    "filename": "some.tv.show",
                    "skip": False,
                    "finished": True,
                    "size": self.tvFile.size,
                    "streamable": True,
                    "localpath": self.tvFile.path.localpathstr,
                    "ismovie": self.tvFile.isMovie(),
                    "watched": False,
                    "displayname": "some.tv.show",
                }
            ],
        }
        actual = dict(response.data)

        self.assertEqual(expected, actual)

    def test_create_tvfile_using_tvpath(self):
        self.data = {
            "filename": "new file",
            "skip": False,
            "finished": True,
            "size": 100,
            "path": self.tvPath.id,
            "streamable": True,
        }
        response = self.client.post(reverse("mediaviewer:api:tv-list"), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        updatedTvPath = Path.objects.get(pk=self.tvPath.id)
        self.assertTrue(updatedTvPath.lastCreatedFileDate is not None)

    def test_create_tvfile_using_moviepath(self):
        self.data = {
            "filename": "new file",
            "skip": False,
            "finished": True,
            "size": 100,
            "path": self.moviePath.id,
            "streamable": True,
        }
        response = self.client.post(reverse("mediaviewer:api:tv-list"), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        updatedMoviePath = Path.objects.get(pk=self.moviePath.id)
        self.assertTrue(updatedMoviePath.lastCreatedFileDate is None)

    def test_update_valid_tvfile(self):
        self.data = {
            "filename": "new.tv.filename",
            "skip": True,
            "finished": True,
            "size": 0,
            "streamable": True,
        }
        response = self.client.put(
            reverse("mediaviewer:api:tv-detail", args=[self.tvFile.id]), self.data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tvFile = File.objects.get(pk=response.data["pk"])
        for k, v in self.data.items():
            expected = v
            actual = getattr(tvFile, k)
            self.assertEqual(
                expected,
                actual,
                "attr: %s expected: %s actual: %s" % (k, expected, actual),
            )

    def test_update_invalid_tvfile(self):
        self.data = {
            "filename": "new.tv.filename",
            "skip": True,
            "finished": True,
            "size": 0,
            "streamable": True,
        }
        response = self.client.put(
            reverse("mediaviewer:api:tv-detail", args=[self.movieFile.id]), self.data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
@pytest.mark.parametrize("tv_or_movie", ("tv", "movie"))
class TestBasicAuthAPIAccess:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.client = APIClient()

        self.tvPath = Path()
        self.tvPath.localpathstr = "/some/local/path"
        self.tvPath.remotepathstr = "/some/local/path"
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = "a.server"
        self.tvPath.save()

        self.anotherTvPath = Path()
        self.anotherTvPath.localpathstr = "/path/to/folder"
        self.anotherTvPath.remotepathstr = "/path/to/folder"
        self.anotherTvPath.skip = False
        self.anotherTvPath.is_movie = False
        self.anotherTvPath.server = "a.server"
        self.anotherTvPath.save()

        self.tvFile = File()
        self.tvFile.filename = "some.tv.show"
        self.tvFile.skip = False
        self.tvFile.finished = True
        self.tvFile.size = 100
        self.tvFile.streamable = True
        self.tvFile.path = self.tvPath
        self.tvFile.hide = False
        self.tvFile.save()

        self.anotherTvFile = File()
        self.anotherTvFile.filename = "another.tv.show"
        self.anotherTvFile.skip = False
        self.anotherTvFile.finished = True
        self.anotherTvFile.size = 100
        self.anotherTvFile.streamable = True
        self.anotherTvFile.path = self.anotherTvPath
        self.anotherTvFile.hide = False
        self.anotherTvFile.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = "/another/local/path"
        self.moviePath.remotepathstr = "/another/local/path"
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = "a.server"
        self.moviePath.save()

        self.movieFile = File()
        self.movieFile.filename = "some.movie.show"
        self.movieFile.skip = False
        self.movieFile.finished = True
        self.movieFile.size = 0
        self.movieFile.streamable = True
        self.movieFile.path = self.moviePath
        self.movieFile.hide = False
        self.movieFile.save()

        self.password = "password"
        self.test_super_user = User.objects.create_superuser(
            "test_super_user", "test@super_user.com", self.password
        )

        self.test_user = UserSettings.new(
            "test_user",
            "test@user.com",
            group=Group.objects.create(),
        )
        self.test_user.set_password(self.password)
        self.test_user.save()

    @pytest.mark.parametrize("user_type", ("regular", "super"))
    def test_path(self, user_type, tv_or_movie):
        if user_type == "regular":
            user = self.test_user
        else:
            user = self.test_super_user

        if tv_or_movie == "tv":
            path_id = self.tvPath.id
        else:
            path_id = self.moviePath.id

        with override_settings(AXES_ENABLED=False):
            self.client.login(username=user.username, password=self.password)
        response = self.client.get(
            reverse(f"mediaviewer:api:{tv_or_movie}-list"), {"pathid": path_id}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_unauthorized_user(self, tv_or_movie):
        if tv_or_movie == "tv":
            path_id = self.tvPath.id
        else:
            path_id = self.moviePath.id

        response = self.client.get(
            reverse(f"mediaviewer:api:{tv_or_movie}-list"), {"pathid": path_id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
