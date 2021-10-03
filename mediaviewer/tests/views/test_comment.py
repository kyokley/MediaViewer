from django.test import TestCase
from mediaviewer.views.comment import comment
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from django.contrib.auth.models import User

import mock


class TestComment(TestCase):
    def setUp(self):
        self.path = Path.objects.create(localpathstr='local.path',
                                        remotepathstr='remote.path',
                                        is_movie=True)
        self.file = File.new('test.filename', self.path)

        self.reverse_patcher = mock.patch('mediaviewer.views.comment.reverse')
        self.mock_reverse = self.reverse_patcher.start()
        self.addCleanup(self.reverse_patcher.stop)

        self.HttpResponseRedirect_patcher = mock.patch('mediaviewer.views.comment.HttpResponseRedirect')
        self.mock_httpResponseRedirect = self.HttpResponseRedirect_patcher.start()
        self.addCleanup(self.HttpResponseRedirect_patcher.stop)

        self.posterfile_new_patcher = mock.patch('mediaviewer.models.file.PosterFile.new')
        self.mock_posterfile_new = self.posterfile_new_patcher.start()
        self.addCleanup(self.posterfile_new_patcher.stop)

        self.request = mock.MagicMock()

        self.user = User.objects.create_superuser('test_user',
                                                  'test@user.com',
                                                  'password')
        # self.user.is_authenticated = True

        settings = mock.MagicMock()
        settings.force_password_change = False
        self.user.settings = lambda : settings

        self.request.user = self.user
        self.request.POST = {'comment': 'comment',
                             'viewed': 'viewed',
                             'search': 'search',
                             'imdb_id': 'imdb_id',
                             'episode_name': 'episode_name',
                             'season': 'season',
                             'episode_number': 'episode_number',
                             'hidden': 'hidden'}

    def test_user_not_staff_movie_comment(self):
        self.request.user.is_staff = False

        expected = self.mock_httpResponseRedirect.return_value
        actual = comment(self.request, self.file.id)

        self.file.refresh_from_db()

        self.assertEqual(expected, actual)
        self.mock_reverse.assert_called_once_with('mediaviewer:results', args=(self.file.id,))
        self.mock_httpResponseRedirect.assert_called_once_with(self.mock_reverse.return_value)

        self.assertTrue(self.file.imdb_id != self.request.POST.get('imdb_id'))
        self.assertTrue(self.file.override_filename != self.request.POST.get('episode_name'))
        self.assertTrue(self.file.override_season != self.request.POST.get('season'))
        self.assertTrue(self.file.override_episode != self.request.POST.get('episode_number'))

    def test_user_is_staff_movie_comment(self):
        self.request.user.is_staff = True

        expected = self.mock_httpResponseRedirect.return_value
        actual = comment(self.request, self.file.id)

        self.file.refresh_from_db()

        self.assertEqual(expected, actual)
        self.mock_reverse.assert_called_once_with('mediaviewer:results', args=(self.file.id,))
        self.mock_httpResponseRedirect.assert_called_once_with(self.mock_reverse.return_value)

        self.assertFalse(self.file.imdb_id != self.request.POST.get('imdb_id'))
        self.assertFalse(self.file.override_filename != self.request.POST.get('episode_name'))
        self.assertFalse(self.file.override_season != self.request.POST.get('season'))
        self.assertFalse(self.file.override_episode != self.request.POST.get('episode_number'))

    def test_user_not_staff_tv_comment(self):
        self.request.user.is_staff = False
        self.path.is_movie = False

        expected = self.mock_httpResponseRedirect.return_value
        actual = comment(self.request, self.file.id)

        self.file.refresh_from_db()

        self.assertEqual(expected, actual)
        self.mock_reverse.assert_called_once_with('mediaviewer:results', args=(self.file.id,))
        self.mock_httpResponseRedirect.assert_called_once_with(self.mock_reverse.return_value)

        self.assertTrue(self.file.imdb_id != self.request.POST.get('imdb_id'))
        self.assertTrue(self.file.override_filename != self.request.POST.get('episode_name'))
        self.assertTrue(self.file.override_season != self.request.POST.get('season'))
        self.assertTrue(self.file.override_episode != self.request.POST.get('episode_number'))

    def test_user_is_staff_tv_comment(self):
        self.request.user.is_staff = True
        self.path.is_movie = False
        self.path.save()

        expected = self.mock_httpResponseRedirect.return_value
        actual = comment(self.request, self.file.id)

        self.file.refresh_from_db()

        self.assertEqual(expected, actual)
        self.mock_reverse.assert_called_once_with('mediaviewer:results', args=(self.file.id,))
        self.mock_httpResponseRedirect.assert_called_once_with(self.mock_reverse.return_value)

        self.assertFalse(self.file.imdb_id != self.request.POST.get('imdb_id'))
        self.assertFalse(self.file.override_filename != self.request.POST.get('episode_name'))
        self.assertFalse(self.file.override_season != self.request.POST.get('season'))
        self.assertFalse(self.file.override_episode != self.request.POST.get('episode_number'))
