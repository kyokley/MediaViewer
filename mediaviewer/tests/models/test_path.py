import mock

from datetime import datetime, timedelta

from django.utils.timezone import utc
from django.test import TestCase

from mediaviewer.models.path import Path
from mediaviewer.models.file import File


class TestProperties(TestCase):
    def setUp(self):
        self.local_path = '/local/path/to/dir'
        self.remote_path = '/remote/path/to/dir'
        self.path_obj = Path.objects.create(
            localpathstr=self.local_path,
            remotepathstr=self.remote_path,
            is_movie=True,
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
        self.path_obj = Path.objects.create(
            localpathstr=self.local_path,
            remotepathstr=self.remote_path,
            is_movie=False,
            skip=False,
            server='localhost')

        expected = '<a href="/mediaviewer/tvshows/{}/">Dir</a>'.format(
            self.path_obj.id)
        actual = self.path_obj.url()

        self.assertEqual(expected, actual)

    def test_url_for_movie(self):
        self.path_obj = Path.objects.create(
            localpathstr=self.local_path,
            remotepathstr=self.remote_path,
            is_movie=True,
            skip=False,
            server='localhost')

        with self.assertRaises(TypeError):
            self.path_obj.url()


class TestDisplayName(TestCase):
    def setUp(self):
        self.local_path = '/local/path/to/dir/this.is.a.test.dir'
        self.remote_path = '/remote/path/to/dir'
        self.path_obj = Path.objects.create(
            localpathstr=self.local_path,
            remotepathstr=self.remote_path,
            is_movie=True,
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
        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_path2 = Path.objects.create(localpathstr='tv.local.path',
                                            remotepathstr='another.remote.path',
                                            is_movie=False)
        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
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


class TestLastCreatedFileDateForSpan(TestCase):
    def setUp(self):
        self.path = Path.objects.create(localpathstr='tv.local.path',
                                        remotepathstr='tv.remote.path',
                                        is_movie=False)

    def test_with_lastCreatedFileDate(self):
        self.path.lastCreatedFileDate = datetime(2018, 11, 1, 0, 0, 0, 0, utc)
        self.path.save()

        expected = '2018-11-01'
        actual = self.path.lastCreatedFileDateForSpan()

        self.assertEqual(expected, actual)

    def test_no_lastCreatedFileDate(self):
        expected = None
        actual = self.path.lastCreatedFileDateForSpan()

        self.assertEqual(expected, actual)


class TestDistinctShowFolders(TestCase):
    def setUp(self):
        buildDistinctShowFoldersFromPaths_patcher = mock.patch(
            'mediaviewer.models.path.Path._buildDistinctShowFoldersFromPaths')
        self.mock_buildDistinctShowFolderFromPaths = (
            buildDistinctShowFoldersFromPaths_patcher.start())
        self.addCleanup(buildDistinctShowFoldersFromPaths_patcher.stop)

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_file = File.new('tv.file', self.tv_path)

        self.tv_path2 = Path.objects.create(localpathstr='tv.local.path2',
                                            remotepathstr='tv.remote.path2',
                                            is_movie=False)
        self.tv_file2 = File.new('tv.file2', self.tv_path2)

        self.hidden_tv_path = Path.objects.create(localpathstr='hidden.local.path',
                                                  remotepathstr='hidden.remote.path',
                                                  is_movie=False)
        self.hidden_tv_file = File.new(
            'hidden.file',
            self.hidden_tv_path,
            hide=True)

        self.another_tv_path = Path.objects.create(localpathstr='another.tv.local.path',
                                                   remotepathstr='another.tv.remote.path',
                                                   is_movie=False)

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('movie.file', self.movie_path)

    def test_distinctShowFolders(self):
        expected = self.mock_buildDistinctShowFolderFromPaths.return_value
        actual = Path.distinctShowFolders()

        self.assertEqual(expected, actual)
        self.mock_buildDistinctShowFolderFromPaths.assert_called_once_with(
            set([self.tv_path, self.tv_path2]))


class TestBuildDistinctShowFoldersFromPaths(TestCase):
    def setUp(self):
        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)

        self.tv_path2 = Path.objects.create(localpathstr='tv.local.path2',
                                            remotepathstr='tv.remote.path2',
                                            is_movie=False)
        self.tv_path2.lastCreatedFileDate = (
            datetime.now(utc) + timedelta(hours=1))

        self.tv_path3 = Path.objects.create(localpathstr='tv.local.path2',
                                            remotepathstr='another.tv.remote.path',
                                            is_movie=False)
        self.tv_path3.lastCreatedFileDate = datetime.now(utc)

    def test_buildDistinctShowFoldersFromPaths(self):
        expected = {
            'tv.local.path': self.tv_path,
            'tv.local.path2': self.tv_path2}
        actual = Path._buildDistinctShowFoldersFromPaths([
            self.tv_path,
            self.tv_path2,
            self.tv_path3])

        self.assertEqual(expected, actual)


class TestDestroy(TestCase):
    def setUp(self):
        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_path_file = File.new('tv.file', self.tv_path)
        self.tv_path_file2 = File.new('tv.file2', self.tv_path)

        self.tv_path2 = Path.objects.create(localpathstr='tv.local.path2',
                                            remotepathstr='tv.remote.path2',
                                            is_movie=False)
        self.tv_path2_file = File.new('tv.file', self.tv_path2)

    def test_destroy(self):
        self.tv_path.destroy()

        self.assertEqual(set(Path.objects.all()), set([self.tv_path2]))
        self.assertEqual(set(File.objects.all()), set([self.tv_path2_file]))
