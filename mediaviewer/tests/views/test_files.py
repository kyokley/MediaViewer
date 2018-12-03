import mock

from django.test import TestCase
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


class TestMovies(TestCase):
    def setUp(self):
        movies_ordered_by_id_patcher = mock.patch(
                'mediaviewer.views.files.File.movies_ordered_by_id')
        self.mock_movies_ordered_by_id = movies_ordered_by_id_patcher.start()
        self.addCleanup(movies_ordered_by_id_patcher.stop)

        setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.files.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        render_patcher = mock.patch(
                'mediaviewer.views.files.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
                                   is_movie=True)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.movie_file = File.new('movie.file', self.movie_path)

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
                'files': self.mock_movies_ordered_by_id.return_value,
                'view': 'movies',
                'LOCAL_IP': LOCAL_IP,
                'BANGUP_IP': BANGUP_IP,
                'can_download': True,
                'jump_to_last': True,
                'active_page': 'movies',
                'title': 'Movies',
                }
        expected = self.mock_render.return_value
        actual = movies(self.request)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=True,
                )
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/files.html',
                expected_context,
                )
        self.mock_movies_ordered_by_id.assert_called_once_with()

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = movies(self.request, self.tv_file.id)

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with(self.request)


class TestMovieByGenre404(TestCase):
    def setUp(self):
        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        self.assertRaises(Http404,
                          movies_by_genre,
                          self.request,
                          100)


class TestMoviesByGenre(TestCase):
    def setUp(self):
        get_object_or_404_patcher = mock.patch(
                'mediaviewer.views.files.get_object_or_404')
        self.mock_get_object_or_404 = get_object_or_404_patcher.start()
        self.addCleanup(get_object_or_404_patcher.stop)

        files_movies_by_genre = mock.patch(
                'mediaviewer.views.files.File.movies_by_genre')
        self.mock_files_movies_by_genre = files_movies_by_genre.start()
        self.addCleanup(files_movies_by_genre.stop)

        setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.files.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        render_patcher = mock.patch(
                'mediaviewer.views.files.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        self.genre = mock.MagicMock(Genre)
        self.genre.id = 123
        self.genre.genre = 'test_genre'

        self.mock_get_object_or_404.return_value = self.genre

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
                                   is_movie=True)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.movie_file = File.new('movie.file', self.movie_path)

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
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

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with(self.request)

    def test_valid(self):
        expected_context = {
                'files': self.mock_files_movies_by_genre.return_value,
                'view': 'movies',
                'LOCAL_IP': LOCAL_IP,
                'BANGUP_IP': BANGUP_IP,
                'can_download': True,
                'jump_to_last': True,
                'active_page': 'movies',
                'title': 'Movies: test_genre',
                }
        expected = self.mock_render.return_value
        actual = movies_by_genre(self.request, self.genre.id)

        self.assertEqual(expected, actual)
        self.mock_files_movies_by_genre.assert_called_once_with(
                self.genre)
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
                self.request,
                'mediaviewer/files.html',
                expected_context)


class TestTvShowSummary(TestCase):
    def setUp(self):
        distinctShowFolders_patcher = mock.patch(
                'mediaviewer.views.files.Path.distinctShowFolders')
        self.mock_distinctShowFolders = distinctShowFolders_patcher.start()
        self.addCleanup(distinctShowFolders_patcher.stop)

        setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.files.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        render_patcher = mock.patch(
                'mediaviewer.views.files.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        self.test_distinct_folders = {
                'test1': 'path1',
                'test2': 'path2',
                }
        self.mock_distinctShowFolders.return_value = self.test_distinct_folders

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
                'pathSet': ['path1', 'path2'],
                'active_page': 'tvshows',
                'title': 'TV Shows',
                }

        expected = self.mock_render.return_value
        actual = tvshowsummary(self.request)

        self.assertEqual(expected, actual)
        self.mock_distinctShowFolders.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=True)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/tvsummary.html',
                expected_context)

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = tvshowsummary(self.request)

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with(self.request)


class TestTvShowByGenre404(TestCase):
    def setUp(self):
        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        self.assertRaises(Http404,
                          tvshows_by_genre,
                          self.request,
                          100)


class TestTvShowsByGenre(TestCase):
    def setUp(self):
        get_object_or_404_patcher = mock.patch(
                'mediaviewer.views.files.get_object_or_404')
        self.mock_get_object_or_404 = get_object_or_404_patcher.start()
        self.addCleanup(get_object_or_404_patcher.stop)

        setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.files.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        render_patcher = mock.patch(
                'mediaviewer.views.files.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        distinctShowFoldersByGenre_patcher = mock.patch(
                'mediaviewer.views.files.Path.distinctShowFoldersByGenre')
        self.mock_distinctShowFoldersByGenre = (
                distinctShowFoldersByGenre_patcher.start())
        self.addCleanup(distinctShowFoldersByGenre_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        self.genre = mock.MagicMock(Genre)
        self.genre.id = 123
        self.genre.genre = 'test_genre'

        self.mock_get_object_or_404.return_value = self.genre

        self.test_distinct_folders = {
                'test1': 'path1',
                'test2': 'path2',
                }
        self.mock_distinctShowFoldersByGenre.return_value = (
                self.test_distinct_folders)

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_valid(self):
        expected_context = {
                'pathSet': ['path1', 'path2'],
                'active_page': 'tvshows',
                'title': 'TV Shows: test_genre',
                }

        expected = self.mock_render.return_value
        actual = tvshows_by_genre(self.request, self.genre.id)

        self.assertEqual(expected, actual)
        self.mock_get_object_or_404.assert_called_once_with(
                Genre,
                pk=self.genre.id)
        self.mock_distinctShowFoldersByGenre.assert_called_once_with(
                self.genre)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=True)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/tvsummary.html',
                expected_context)

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = tvshows_by_genre(self.request, self.genre.id)

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with(self.request)


class TestTvShow404(TestCase):
    def setUp(self):
        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_404(self):
        self.assertRaises(Http404,
                          tvshows,
                          self.request,
                          100)


class TestTvShows(TestCase):
    def setUp(self):
        get_object_or_404_patcher = mock.patch(
                'mediaviewer.views.files.get_object_or_404')
        self.mock_get_object_or_404 = get_object_or_404_patcher.start()
        self.addCleanup(get_object_or_404_patcher.stop)

        files_by_localpath_patcher = mock.patch(
                'mediaviewer.views.files.File.files_by_localpath')
        self.mock_files_by_localpath = files_by_localpath_patcher.start()
        self.addCleanup(files_by_localpath_patcher.stop)

        setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.files.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        render_patcher = mock.patch(
                'mediaviewer.views.files.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        self.change_password_patcher = mock.patch(
                'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()
        self.addCleanup(self.change_password_patcher.stop)

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
                                   is_movie=True)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.movie_file = File.new('movie.file', self.movie_path)

        self.mock_get_object_or_404.return_value = self.tv_path
        self.mock_files_by_localpath.return_value = [self.tv_file]

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
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

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with(self.request)

    def test_valid(self):
        expected_context = {
                'files': [self.tv_file],
                'path': self.tv_path,
                'view': 'tvshows',
                'LOCAL_IP': LOCAL_IP,
                'BANGUP_IP': BANGUP_IP,
                'can_download': True,
                'jump_to_last': True,
                'active_page': 'tvshows',
                'title': 'Tv Local Path',
                'long_plot': False,
                }

        expected = self.mock_render.return_value
        actual = tvshows(self.request, self.tv_path.id)

        self.assertEqual(expected, actual)
        self.mock_get_object_or_404.assert_called_once_with(
                Path,
                pk=self.tv_path.id)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request,
                includeMessages=True)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/files.html',
                expected_context)


class TestAjaxReport404(TestCase):
    def setUp(self):
        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        settings = self.user.settings()
        settings.force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {'reportid': 'file-100'}

    def test_404(self):
        self.assertRaises(Http404,
                          ajaxreport,
                          self.request,
                          )


class TestAjaxReport(TestCase):
    def setUp(self):
        get_object_or_404_patcher = mock.patch(
                'mediaviewer.views.files.get_object_or_404')
        self.mock_get_object_or_404 = get_object_or_404_patcher.start()
        self.addCleanup(get_object_or_404_patcher.stop)

        createNewMessage_patcher = mock.patch(
                'mediaviewer.views.files.Message.createNewMessage')
        self.mock_createNewMessage = (
                createNewMessage_patcher.start())
        self.addCleanup(createNewMessage_patcher.stop)

        HttpResponse_patcher = mock.patch(
                'mediaviewer.views.files.HttpResponse')
        self.mock_HttpResponse = HttpResponse_patcher.start()
        self.addCleanup(HttpResponse_patcher.stop)

        dumps_patcher = mock.patch(
                'mediaviewer.views.files.json.dumps')
        self.mock_dumps = dumps_patcher.start()
        self.addCleanup(dumps_patcher.stop)

        self.fake_file = mock.MagicMock(File)
        self.fake_file.filename = 'test_filename'
        self.mock_get_object_or_404.return_value = self.fake_file

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.staff_user = UserSettings.new(
                'test_staff_user',
                'a@b.com',
                send_email=False)
        self.staff_user.is_staff = True
        self.staff_user.save()

        self.user = UserSettings.new(
                'test_user',
                'b@c.com',
                send_email=False)

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
        self.request.POST = {'reportid': 'file-123'}

    def test_valid(self):
        expected_response = {
                'errmsg': '',
                'reportid': 123,
                }

        expected = self.mock_HttpResponse.return_value
        actual = ajaxreport(self.request)

        self.assertEqual(expected, actual)
        self.mock_get_object_or_404.assert_called_once_with(
                File,
                pk=123)
        self.mock_createNewMessage.assert_called_once_with(
                self.staff_user,
                'test_filename has been reported by test_user',
                level=messages.WARNING)
        self.mock_dumps.assert_called_once_with(
                expected_response)
        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                content_type='application/javascript')
