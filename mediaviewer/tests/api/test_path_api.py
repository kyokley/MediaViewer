import pytest

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from mediaviewer.models.path import Path


class TvPathViewSetTests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )

        self.client.login(username="test_user", password="password")

        self.tvPath = Path()
        self.tvPath.localpathstr = "/some/local/path"
        self.tvPath.remotepathstr = "/some/local/path"
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = "a.server"
        self.tvPath.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = "/another/local/path"
        self.moviePath.remotepathstr = "/another/local/path"
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = "a.server"
        self.moviePath.save()

    def test_create_tv_path_exists(self):
        self.data = {
            "localpath": "/some/local/path",
            "remotepath": "/some/local/path",
            "server": "fake.server",
            "skip": False,
        }
        response = self.client.post(reverse("mediaviewer:api:tvpath-list"), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_dict = {
            "localpath": "/some/local/path",
            "remotepath": "/some/local/path",
            "skip": False,
            "server": "a.server",
            "is_movie": False,
            "finished": False,
        }

        pk = response.data["pk"]
        path = Path.objects.get(pk=pk)
        for k, v in expected_dict.items():
            expected = v
            actual = getattr(path, k)
            self.assertEqual(
                expected,
                actual,
                f"attr: {k} expected: {expected} actual: {actual}",
            )

    def test_create_tvpath(self):
        self.data = {
            "localpath": "/path/to/folder",
            "remotepath": "/path/to/folder",
            "server": "a.server",
            "skip": False,
        }
        response = self.client.post(reverse("mediaviewer:api:tvpath-list"), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        expected_dict = self.data
        expected_dict.update({"is_movie": False})

        pk = response.data["pk"]
        path = Path.objects.get(pk=pk)
        for k, v in expected_dict.items():
            expected = v
            actual = getattr(path, k)
            self.assertEqual(
                expected,
                actual,
                f"attr: {k} expected: {expected} actual: {actual}",
            )

    def test_get_path_detail(self):
        response = self.client.get(
            reverse("mediaviewer:api:tvpath-detail", args=[self.tvPath.id])
        )
        for k, v in response.data.items():
            actual = v
            if not hasattr(self.tvPath, k):
                continue
            expected = getattr(self.tvPath, k)
            expected = (
                expected(self.test_user) if hasattr(expected, "__call__") else expected
            )
            self.assertEqual(
                expected,
                actual,
                f"attr: {k} expected: {expected} actual: {actual}",
            )

    def test_get_path_list(self):
        response = self.client.get(reverse("mediaviewer:api:tvpath-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.tvPath.id,
                    "localpath": "/some/local/path",
                    "remotepath": "/some/local/path",
                    "server": "a.server",
                    "skip": False,
                    "number_of_unwatched_shows": 0,
                    "is_movie": False,
                    "finished": False,
                    "short_name": "path",
                }
            ],
        }
        actual = dict(response.data)

        self.assertEqual(expected, actual)


@pytest.mark.django_db
class TestUnfinishedTVPaths:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )

        self.client = APIClient()
        self.client.login(username="test_user", password="password")

        self.tvPath = Path()
        self.tvPath.localpathstr = "/some/local/path"
        self.tvPath.remotepathstr = "/some/local/path"
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = "a.server"
        self.tvPath.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = "/another/local/path"
        self.moviePath.remotepathstr = "/another/local/path"
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = "a.server"
        self.moviePath.save()

        self.finishedTvPath = Path()
        self.finishedTvPath.localpathstr = "/some/local/finished/path"
        self.finishedTvPath.remotepathstr = "/some/local/finished/path"
        self.finishedTvPath.skip = False
        self.finishedTvPath.is_movie = False
        self.finishedTvPath.server = "a.server"
        self.finishedTvPath.finished = True
        self.finishedTvPath.save()

    def test_unfinished_list_only(self):
        response = self.client.get(
            reverse("mediaviewer:api:tvpath-list"), {"finished": False}
        )
        assert response.status_code == status.HTTP_200_OK

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.tvPath.id,
                    "localpath": "/some/local/path",
                    "remotepath": "/some/local/path",
                    "server": "a.server",
                    "skip": False,
                    "number_of_unwatched_shows": 0,
                    "is_movie": False,
                    "finished": False,
                    "short_name": "path",
                }
            ],
        }
        actual = dict(response.data)

        assert expected == actual

    def test_finished_list_only(self):
        response = self.client.get(
            reverse("mediaviewer:api:tvpath-list"), {"finished": True}
        )
        assert response.status_code == status.HTTP_200_OK

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.finishedTvPath.id,
                    "localpath": "/some/local/finished/path",
                    "remotepath": "/some/local/finished/path",
                    "server": "a.server",
                    "skip": False,
                    "number_of_unwatched_shows": 0,
                    "is_movie": False,
                    "finished": True,
                    "short_name": "path",
                }
            ],
        }
        actual = dict(response.data)

        assert expected == actual

    def test_bad_finished_query_param(self):
        self.finishedTvPath = Path()
        self.finishedTvPath.localpathstr = "/some/local/finished/path"
        self.finishedTvPath.remotepathstr = "/some/local/finished/path"
        self.finishedTvPath.skip = False
        self.finishedTvPath.is_movie = False
        self.finishedTvPath.server = "a.server"
        self.finishedTvPath.finished = True
        self.finishedTvPath.save()

        response = self.client.get(
            reverse("mediaviewer:api:tvpath-list"), {"finished": "asdf"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class MoviePathViewSetTests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_superuser(
            "test_user", "test@user.com", "password"
        )
        self.client.login(username="test_user", password="password")

        self.tvPath = Path()
        self.tvPath.localpathstr = "/some/local/path"
        self.tvPath.remotepathstr = "/some/local/path"
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = "a.server"
        self.tvPath.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = "/another/local/path"
        self.moviePath.remotepathstr = "/another/local/path"
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = "a.server"
        self.moviePath.finished = False
        self.moviePath.save()

    def test_create_moviepath_exists(self):
        self.data = {
            "localpath": "/another/local/path",
            "remotepath": "/another/local/path",
            "server": "fake.server",
            "skip": False,
        }
        response = self.client.post(
            reverse("mediaviewer:api:moviepath-list"), self.data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_dict = {
            "localpath": "/another/local/path",
            "remotepath": "/another/local/path",
            "skip": False,
            "server": "a.server",
            "is_movie": True,
            "finished": False,
        }

        pk = response.data["pk"]
        path = Path.objects.get(pk=pk)
        for k, v in expected_dict.items():
            expected = v
            actual = getattr(path, k)
            self.assertEqual(
                expected,
                actual,
                f"attr: {k} expected: {expected} actual: {actual}",
            )

    def test_create_moviepath(self):
        self.data = {
            "localpath": "/path/to/folder",
            "remotepath": "/path/to/folder",
            "server": "a.server",
            "skip": False,
        }
        response = self.client.post(
            reverse("mediaviewer:api:moviepath-list"), self.data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        expected_dict = self.data
        expected_dict.update({"is_movie": True})

        pk = response.data["pk"]
        path = Path.objects.get(pk=pk)
        for k, v in expected_dict.items():
            expected = v
            actual = getattr(path, k)
            self.assertEqual(
                expected,
                actual,
                f"attr: {k} expected: {expected} actual: {actual}",
            )

    def test_get_moviepath(self):
        response = self.client.get(
            reverse("mediaviewer:api:moviepath-detail", args=[self.moviePath.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {
            "skip": False,
            "number_of_unwatched_shows": 0,
            "localpath": u"/another/local/path",
            "server": u"a.server",
            "remotepath": u"/another/local/path",
            "pk": self.moviePath.id,
            "finished": False,
            "is_movie": True,
            "short_name": "path",
        }

        self.assertEqual(expected, response.data)

    def test_get_moviepath_list(self):
        response = self.client.get(reverse("mediaviewer:api:moviepath-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.moviePath.id,
                    "localpath": "/another/local/path",
                    "remotepath": "/another/local/path",
                    "server": "a.server",
                    "skip": False,
                    "number_of_unwatched_shows": 0,
                    "is_movie": True,
                    "finished": False,
                    "short_name": "path",
                }
            ],
        }
        actual = dict(response.data)

        self.assertEqual(expected, actual)
