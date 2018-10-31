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

from mediaviewer.views.files import movies


class TestMovies(TestCase):
    def setUp(self):
        File_movies_patcher = mock.patch(
                'mediaviewer.views.files.File.movies')
        self.mock_File_movies = File_movies_patcher.start()
        self.addCleanup(File_movies_patcher.stop)

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
                'files': (
                    self.mock_File_movies.return_value
                                         .filter
                                         .return_value
                                         .order_by
                                         .return_value),
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

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = movies(self.request, self.tv_file.id)

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with(self.request)
