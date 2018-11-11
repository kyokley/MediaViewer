import mock
from django.test import TestCase

from mediaviewer.models.path import Path
from mediaviewer.models.file import File


class TestProperties(TestCase):
    def setUp(self):
        self.local_path = '/local/path/to/dir'
        self.remote_path = '/remote/path/to/dir'
        self.path_obj = Path.new(
                self.local_path,
                self.remote_path,
                True,
                skip=False,
                server='localhost')

    def test_new(self):
        self.assertEqual(self.path_obj.localpathstr, self.local_path)
        self.assertEqual(self.path_obj.remotepathstr, self.remote_path)
        self.assertEqual(self.path_obj.is_movie, True)
        self.assertEqual(self.path_obj.skip, False)
        self.assertEqual(self.path_obj.server, 'localhost')

    def test_shortName(self):
        expected = 'dir'
        actual = self.path_obj.shortName
        self.assertEqual(expected, actual)

    def test_localPath(self):
        expected = self.local_path
        actual = self.path_obj.localPath
        self.assertEqual(expected, actual)

    def test_remotePath(self):
        expected = self.remote_path
        actual = self.path_obj.remotePath
        self.assertEqual(expected, actual)


class TestUrl(TestCase):
    def setUp(self):
        self.local_path = '/local/path/to/dir'
        self.remote_path = '/remote/path/to/dir'

    def test_url_for_tv(self):
        self.path_obj = Path.new(
                self.local_path,
                self.remote_path,
                False,
                skip=False,
                server='localhost')

        expected = '<a href="/mediaviewer/tvshows/{}/">Dir</a>'.format(
                self.path_obj.id)
        actual = self.path_obj.url()

        self.assertEqual(expected, actual)

    def test_url_for_movie(self):
        self.path_obj = Path.new(
                self.local_path,
                self.remote_path,
                True,
                skip=False,
                server='localhost')

        with self.assertRaises(TypeError):
            self.path_obj.url()


class TestDisplayName(TestCase):
    def setUp(self):
        self.local_path = '/local/path/to/dir/this.is.a.test.dir'
        self.remote_path = '/remote/path/to/dir'
        self.path_obj = Path.new(
                self.local_path,
                self.remote_path,
                True,
                skip=False,
                server='localhost')

    def test_no_override(self):
        expected = 'This Is A Test Dir'
        actual = self.path_obj.displayName()

        self.assertEqual(expected, actual)

    def test_with_override(self):
        self.path_obj.override_display_name = 'Overridden Name'

        self.assertEqual('Overridden Name',
                         self.path_obj.displayName())


class TestFiles(TestCase):
    def setUp(self):
        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.tv_path2 = Path.new('tv.local.path',
                                 'another.remote.path',
                                 is_movie=False)
        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
                                   is_movie=True)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file2 = File.new('tv.file2', self.tv_path)
        self.tv_file3 = File.new('tv.file3', self.tv_path2)
        self.tv_file4 = File.new('tv.file4', self.tv_path2)

        self.hidden_tv_file = File.new(
                'hidden.tv.file',
                self.tv_path,
                hide=True)

        self.movie_file = File.new('movie.file', self.movie_path)
        self.movie_file2 = File.new('movie.file2', self.movie_path)
        self.hidden_movie_file = File.new(
                'hidden.movie.file',
                self.movie_path,
                hide=True)

    def test_files(self):
        expected = set([
            self.tv_file,
            self.tv_file2,
            self.tv_file3,
            self.tv_file4])
        actual = set(self.tv_path.files())

        self.assertEqual(expected, actual)
