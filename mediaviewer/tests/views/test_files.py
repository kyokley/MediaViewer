import mock
import pytest

from django.http import HttpRequest, Http404

from django.contrib import messages
from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import (
    UserSettings,
    LOCAL_IP,
    BANGUP_IP,
)

from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.genre import Genre

from mediaviewer.views.files import (
    movies,
    movies_by_genre,
    tvshowsummary,
    tvshows_by_genre,
    tvshows,
    ajaxreport,
)


@pytest.mark.django_db
class TestMovies:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_movies_ordered_by_id = mocker.patch(
            "mediaviewer.views.files.File.movies_ordered_by_id"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.movie_path = Path.objects.create(
            localpathstr="movie.local.path",
            remotepathstr="movie.remote.path",
            is_movie=True,
        )

        self.tv_file = File.objects.create(filename="tv.file", path=self.tv_path)
        self.movie_file = File.objects.create(
            filename="movie.file", path=self.movie_path
        )

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user",
                                     "a@b.com",
                                     send_email=False,
                                     verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "files": [],
            "view": "movies",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "movies",
            "title": "Movies",
        }
        expected = self.mock_render.return_value
        actual = movies(self.request)

        assert expected == actual
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context,
            self.request,
            includeMessages=True,
        )
        self.mock_render.assert_called_once_with(
            self.request,
            "mediaviewer/files.html",
            expected_context,
        )
        self.mock_movies_ordered_by_id.assert_called_once_with()

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = movies(self.request, self.tv_file.id)

        assert expected == actual
        self.mock_change_password.assert_called_once_with()


@pytest.mark.django_db
class TestMovieByGenre404:
    @pytest.fixture(autouse=True)
    def setUp(self):
        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        with pytest.raises(Http404):
            movies_by_genre(self.request, 100)


@pytest.mark.django_db
class TestMoviesByGenre:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.files.get_object_or_404"
        )

        self.mock_files_movies_by_genre = mocker.patch(
            "mediaviewer.views.files.File.movies_by_genre"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

        self.genre = mock.MagicMock(Genre)
        self.genre.id = 123
        self.genre.genre = "test_genre"

        self.mock_get_object_or_404.return_value = self.genre

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.movie_path = Path.objects.create(
            localpathstr="movie.local.path",
            remotepathstr="movie.remote.path",
            is_movie=True,
        )

        self.tv_file = File.objects.create(filename="tv.file", path=self.tv_path)
        self.movie_file = File.objects.create(
            filename="movie.file", path=self.movie_path
        )

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user",
                                     "a@b.com",
                                     send_email=False,
                                     verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = movies_by_genre(self.request, self.genre.id)

        assert expected == actual
        self.mock_change_password.assert_called_once_with()

    def test_valid(self):
        expected_context = {
            "files": [],
            "view": "movies",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "movies",
            "title": "Movies: test_genre",
        }
        expected = self.mock_render.return_value
        actual = movies_by_genre(self.request, self.genre.id)

        assert expected == actual
        self.mock_files_movies_by_genre.assert_called_once_with(self.genre)
        self.mock_get_object_or_404.assert_called_once_with(
            Genre,
            pk=self.genre.id,
        )
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context,
            self.request,
            includeMessages=True,
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/files.html", expected_context
        )


@pytest.mark.django_db
class TestTvShowSummary:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_distinctShowFolders = mocker.patch(
            "mediaviewer.views.files.Path.distinctShowFolders"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

        self.test_distinct_folders = {
            "test1": "path1",
            "test2": "path2",
        }
        self.mock_distinctShowFolders.return_value = self.test_distinct_folders

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user",
                                     "a@b.com",
                                     send_email=False,
                                     verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "pathSet": ["path1", "path2"],
            "active_page": "tvshows",
            "title": "TV Shows",
        }

        expected = self.mock_render.return_value
        actual = tvshowsummary(self.request)

        assert expected == actual
        self.mock_distinctShowFolders.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/tvsummary.html", expected_context
        )

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = tvshowsummary(self.request)

        assert expected == actual
        self.mock_change_password.assert_called_once_with()


@pytest.mark.django_db
class TestTvShowByGenre404:
    @pytest.fixture(autouse=True)
    def setUp(self):
        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user",
                                     "a@b.com",
                                     send_email=False,
                                     verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        with pytest.raises(Http404):
            tvshows_by_genre(self.request, 100)


@pytest.mark.django_db
class TestTvShowsByGenre:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.files.get_object_or_404"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

        self.mock_distinctShowFoldersByGenre = mocker.patch(
            "mediaviewer.views.files.Path.distinctShowFoldersByGenre"
        )

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.genre = mock.MagicMock(Genre)
        self.genre.id = 123
        self.genre.genre = "test_genre"

        self.mock_get_object_or_404.return_value = self.genre

        self.test_distinct_folders = {
            "test1": "path1",
            "test2": "path2",
        }
        self.mock_distinctShowFoldersByGenre.return_value = self.test_distinct_folders

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user",
                                     "a@b.com",
                                     send_email=False,
                                     verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
            "pathSet": ["path1", "path2"],
            "active_page": "tvshows",
            "title": "TV Shows: test_genre",
        }

        expected = self.mock_render.return_value
        actual = tvshows_by_genre(self.request, self.genre.id)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(Genre, pk=self.genre.id)
        self.mock_distinctShowFoldersByGenre.assert_called_once_with(self.genre)
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/tvsummary.html", expected_context
        )

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = tvshows_by_genre(self.request, self.genre.id)

        assert expected == actual
        self.mock_change_password.assert_called_once_with()


@pytest.mark.django_db
class TestTvShow404:
    @pytest.fixture(autouse=True)
    def setUp(self):
        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user",
                                     "a@b.com",
                                     send_email=False,
                                     verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        with pytest.raises(Http404):
            tvshows(self.request, 100)


@pytest.mark.django_db
class TestTvShows:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.files.get_object_or_404"
        )

        self.mock_files_by_localpath = mocker.patch(
            "mediaviewer.views.files.File.files_by_localpath"
        )

        self.mock_setSiteWideContext = mocker.patch(
            "mediaviewer.views.files.setSiteWideContext"
        )

        self.mock_render = mocker.patch("mediaviewer.views.files.render")

        self.mock_change_password = mocker.patch(
            "mediaviewer.views.password_reset.change_password"
        )

        self.tv_path = Path.objects.create(
            localpathstr="tv.local.path", remotepathstr="tv.remote.path", is_movie=False
        )
        self.movie_path = Path.objects.create(
            localpathstr="movie.local.path",
            remotepathstr="movie.remote.path",
            is_movie=True,
        )

        self.tv_file = File.objects.create(filename="tv.file", path=self.tv_path)
        self.movie_file = File.objects.create(
            filename="movie.file", path=self.movie_path
        )

        self.mock_get_object_or_404.return_value = self.tv_path
        self.mock_files_by_localpath.return_value.select_related.return_value = [
            self.tv_file
        ]

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False, verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = tvshows(self.request, self.tv_path.id)

        assert expected == actual
        self.mock_change_password.assert_called_once_with()

    def test_valid(self):
        expected_context = {
            "files": [
                {
                    "date": self.tv_file.datecreated.date(),
                    "dateCreatedForSpan": self.tv_file.dateCreatedForSpan(),
                    "id": self.tv_file.id,
                    "name": "tv.file",
                    "viewed": False,
                }
            ],
            "path": self.tv_path,
            "view": "tvshows",
            "LOCAL_IP": LOCAL_IP,
            "BANGUP_IP": BANGUP_IP,
            "can_download": True,
            "jump_to_last": True,
            "active_page": "tvshows",
            "title": "Tv Local Path",
            "long_plot": "",
        }

        expected = self.mock_render.return_value
        actual = tvshows(self.request, self.tv_path.id)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(Path, pk=self.tv_path.id)
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context, self.request, includeMessages=True
        )
        self.mock_render.assert_called_once_with(
            self.request, "mediaviewer/files.html", expected_context
        )


@pytest.mark.django_db
class TestAjaxReport404:
    @pytest.fixture(autouse=True)
    def setUp(self):
        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.user = UserSettings.new("test_user", "a@b.com", send_email=False, verified=True)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"reportid": "file-100"}

    def test_404(self):
        with pytest.raises(Http404):
            ajaxreport(self.request)


@pytest.mark.django_db
class TestAjaxReport:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get_object_or_404 = mocker.patch(
            "mediaviewer.views.files.get_object_or_404"
        )

        self.mock_createNewMessage = mocker.patch(
            "mediaviewer.views.files.Message.createNewMessage"
        )

        self.mock_HttpResponse = mocker.patch("mediaviewer.views.files.HttpResponse")

        self.mock_dumps = mocker.patch("mediaviewer.views.files.json.dumps")

        self.fake_file = mock.MagicMock(File)
        self.fake_file.filename = "test_filename"
        self.mock_get_object_or_404.return_value = self.fake_file

        mv_group = Group(name="MediaViewer")
        mv_group.save()

        self.staff_user = UserSettings.new(
            "test_staff_user", "a@b.com", send_email=False, verified=True
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

        self.user = UserSettings.new("test_user", "b@c.com", send_email=False, verified=True)

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {"reportid": "file-123"}

    def test_valid(self):
        expected_response = {
            "errmsg": "",
            "reportid": 123,
        }

        expected = self.mock_HttpResponse.return_value
        actual = ajaxreport(self.request)

        assert expected == actual
        self.mock_get_object_or_404.assert_called_once_with(File, pk=123)
        self.mock_createNewMessage.assert_called_once_with(
            self.staff_user,
            "test_filename has been reported by test_user",
            level=messages.WARNING,
        )
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value, content_type="application/javascript"
        )
