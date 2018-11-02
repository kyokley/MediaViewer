import mock

from django.test import TestCase
from django.http import HttpRequest, Http404

from django.contrib.auth.models import (Group,
                                        AnonymousUser,
                                        )
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


class TestMoviesByGenre(TestCase):
    def setUp(self):
        get_object_or_404_patcher = mock.patch(
                'mediaviewer.views.files.get_object_or_404')
        self.mock_get_object_or_404 = get_object_or_404_patcher.start()
        self.addCleanup(get_object_or_404_patcher.stop)

        movies_by_genre_patcher = mock.patch(
                'mediaviewer.views.files.File.movies_by_genre')
        self.mock_movies_by_genre = movies_by_genre_patcher.start()
        self.addCleanup(movies_by_genre_patcher.stop)

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
                'files': self.mock_movies_by_genre.return_value,
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
