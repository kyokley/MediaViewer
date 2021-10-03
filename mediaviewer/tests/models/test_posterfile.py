import mock
import pytest
from django.test import TestCase

from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

sample_good_result = {u'backdrop_path': u'/asdfasdf.jpg',
                      u'first_air_date': u'2016-09-30',
                      u'genre_ids': [18, 10765],
                      u'id': 12345,
                      u'name': u"show name",
                      u'origin_country': [u'US'],
                      u'original_language': u'en',
                      u'original_name': u"show name",
                      u'overview': u'show description',
                      u'popularity': 4.278642,
                      u'poster_path': u'/zxcvzxcv.jpg',
                      u'vote_average': 6.81,
                      u'vote_count': 41}

sample_good_crew = {'id': 12345,
                    'cast': [{'cast_id': 2345,
                              'character': 'John Doe',
                              'credit_id': '3456',
                              'id': 4567,
                              'name': 'Alex Reporter',
                              'order': 0}],
                    'crew': [{'credit_id': 18365,
                              'department': 'Directing',
                              'id': 582,
                              'job': 'Director',
                              'name': 'Jim Pope',
                              'order': 0},
                             {'credit_id': 18365,
                              'department': 'Directing',
                              'id': 582,
                              'job': 'Director',
                              'name': 'Jim Pope',
                              'order': 0}
                             ],
                    }

sample_bad_result = {u'page': 1,
                     u'results': [],
                     u'total_pages': 1,
                     u'total_results': 0}


class TestNew(TestCase):
    def setUp(self):
        objects_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile.objects')
        self.mock_objects = objects_patcher.start()
        self.addCleanup(objects_patcher.stop)

        populate_poster_data_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._populate_poster_data')
        self.mock_populate_poster_data = populate_poster_data_patcher.start()
        self.addCleanup(populate_poster_data_patcher.stop)

        self.path = Path.objects.create(localpathstr='local.path',
                                        remotepathstr='remote.path',
                                        is_movie=False)
        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.file = File.new('new.file.mp4',
                             self.movie_path)

        self.mock_objects.filter.return_value.first.return_value = None

    def test_no_file_no_path(self):
        self.assertRaises(ValueError,
                          PosterFile.new)

    def test_path_is_movie(self):
        self.assertRaises(ValueError,
                          PosterFile.new,
                          path=self.movie_path)

    def test_file(self):
        new_obj = PosterFile.new(file=self.file)

        self.assertEqual(new_obj.file, self.file)
        self.assertEqual(new_obj.path, None)
        self.mock_populate_poster_data.assert_called_once_with()

    def test_path(self):
        new_obj = PosterFile.new(path=self.path)

        self.assertEqual(new_obj.file, None)
        self.assertEqual(new_obj.path, self.path)
        self.mock_populate_poster_data.assert_called_once_with()

    def test_existing_for_file(self):
        self.mock_objects.filter.return_value.first.return_value = (
            'existing_obj')

        existing = PosterFile.new(file=self.file)
        self.assertEqual(existing, 'existing_obj')
        self.assertFalse(self.mock_populate_poster_data.called)

    def test_existing_for_path(self):
        self.mock_objects.filter.return_value.first.return_value = (
            'existing_obj')

        existing = PosterFile.new(path=self.path)
        self.assertEqual(existing, 'existing_obj')
        self.assertFalse(self.mock_populate_poster_data.called)


class TestGetIMDBData(TestCase):
    def setUp(self):
        getDataFromIMDB_patcher = mock.patch(
            'mediaviewer.models.posterfile.getDataFromIMDB')
        self.mock_getDataFromIMDB = getDataFromIMDB_patcher.start()
        self.addCleanup(getDataFromIMDB_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch(
            'mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        cast_and_crew_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._cast_and_crew')
        self.mock_cast_and_crew = cast_and_crew_patcher.start()
        self.addCleanup(cast_and_crew_patcher.stop)

        assign_tvdb_info_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._assign_tvdb_info')
        self.mock_assign_tvdb_info = assign_tvdb_info_patcher.start()
        self.addCleanup(assign_tvdb_info_patcher.stop)

        store_extended_info_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._store_extended_info')
        self.mock_store_extended_info = store_extended_info_patcher.start()
        self.addCleanup(store_extended_info_patcher.stop)

        store_plot_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._store_plot')
        self.mock_store_plot = store_plot_patcher.start()
        self.addCleanup(store_plot_patcher.stop)

        store_genres_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._store_genres')
        self.mock_store_genres = store_genres_patcher.start()
        self.addCleanup(store_genres_patcher.stop)

        store_rated_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._store_rated')
        self.mock_store_rated = store_rated_patcher.start()
        self.addCleanup(store_rated_patcher.stop)

        self.fake_data = {'Poster': 'test_poster',
                          'id': 123}
        self.mock_getDataFromIMDB.return_value = self.fake_data
        self.mock_getDataFromIMDBByPath.return_value = self.fake_data

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('new.file.mp4',
                                   self.movie_path)

        self.test_obj = PosterFile()

    def test_file_is_movie(self):
        self.test_obj.file = self.movie_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        self.assertEqual(expected, actual)
        self.mock_getDataFromIMDB.assert_called_once_with(self.movie_file)
        self.mock_cast_and_crew.assert_called_once_with()
        self.assertEqual('test_poster', self.test_obj.poster_url)
        self.mock_assign_tvdb_info.assert_called_once_with()
        self.mock_store_extended_info.assert_called_once_with()
        self.mock_store_plot.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_genres.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_rated.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)

    def test_path_for_tv(self):
        self.test_obj.path = self.tv_path

        expected = self.mock_getDataFromIMDBByPath.return_value
        actual = self.test_obj._getIMDBData()

        self.assertEqual(expected, actual)
        self.mock_getDataFromIMDBByPath.assert_called_once_with(self.tv_path)
        self.mock_cast_and_crew.assert_called_once_with()
        self.assertEqual('test_poster', self.test_obj.poster_url)
        self.mock_assign_tvdb_info.assert_called_once_with()

        self.mock_store_extended_info.assert_called_once_with()
        self.mock_store_plot.assert_called_once_with(
            self.mock_getDataFromIMDBByPath.return_value)
        self.mock_store_genres.assert_called_once_with(
            self.mock_getDataFromIMDBByPath.return_value)
        self.mock_store_rated.assert_called_once_with(
            self.mock_getDataFromIMDBByPath.return_value)

    def test_file_for_tv(self):
        self.test_obj.file = self.tv_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        self.assertEqual(expected, actual)
        self.mock_getDataFromIMDB.assert_called_once_with(self.tv_file)
        self.mock_cast_and_crew.assert_called_once_with()
        self.assertEqual('test_poster', self.test_obj.poster_url)
        self.mock_assign_tvdb_info.assert_called_once_with()

        self.mock_store_extended_info.assert_called_once_with()
        self.mock_store_plot.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_genres.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_rated.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)

    def test_no_data_for_movie(self):
        self.mock_getDataFromIMDB.return_value = None
        self.test_obj.file = self.movie_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        self.assertEqual(expected, actual)
        self.mock_getDataFromIMDB.assert_called_once_with(self.movie_file)
        self.assertFalse(self.mock_cast_and_crew.called)
        self.assertEqual(None, self.test_obj.poster_url)
        self.mock_assign_tvdb_info.assert_called_once_with()
        self.assertFalse(self.mock_store_extended_info.called)
        self.assertFalse(self.mock_store_plot.called)
        self.assertFalse(self.mock_store_genres.called)
        self.assertFalse(self.mock_store_rated.called)

    def test_no_data_for_path_for_tv(self):
        self.mock_getDataFromIMDBByPath.return_value = None
        self.test_obj.path = self.tv_path

        expected = self.mock_getDataFromIMDBByPath.return_value
        actual = self.test_obj._getIMDBData()

        self.assertEqual(expected, actual)
        self.mock_getDataFromIMDBByPath.assert_called_once_with(self.tv_path)
        self.assertFalse(self.mock_cast_and_crew.called)
        self.assertEqual(None, self.test_obj.poster_url)
        self.mock_assign_tvdb_info.assert_called_once_with()
        self.assertFalse(self.mock_store_extended_info.called)
        self.assertFalse(self.mock_store_plot.called)
        self.assertFalse(self.mock_store_genres.called)
        self.assertFalse(self.mock_store_rated.called)

    def test_no_data_for_file_for_tv(self):
        self.mock_getDataFromIMDB.return_value = None
        self.test_obj.file = self.tv_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        self.assertEqual(expected, actual)
        self.mock_getDataFromIMDB.assert_called_once_with(self.tv_file)
        self.assertFalse(self.mock_cast_and_crew.called)
        self.assertEqual(None, self.test_obj.poster_url)
        self.assertFalse(self.mock_store_extended_info.called)
        self.assertFalse(self.mock_store_plot.called)
        self.assertFalse(self.mock_store_genres.called)
        self.assertFalse(self.mock_store_rated.called)


class TestCastAndCrew(TestCase):
    def setUp(self):
        getCastData_patcher = mock.patch(
            'mediaviewer.models.posterfile.getCastData')
        self.mock_getCastData = getCastData_patcher.start()
        self.addCleanup(getCastData_patcher.stop)

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('new.file.mp4',
                                   self.movie_path)

        self.test_obj = PosterFile()
        self.test_obj.tmdb_id = 123
        self.test_obj.save()

        self.test_getCastData = {
            'cast': [
                {'name': 'test_actor'}],
            'crew': [
                {'job': 'Writer',
                 'name': 'test_writer'},
                {'job': 'Director',
                 'name': 'test_director'},
            ],
        }
        self.mock_getCastData.return_value = self.test_getCastData

    def test_no_cast_data(self):
        self.mock_getCastData.return_value = None
        self.test_obj.file = self.movie_file

        expected = None
        actual = self.test_obj._cast_and_crew()

        self.assertEqual(expected, actual)
        self.mock_getCastData.assert_called_once_with(
            123,
            season=None,
            episode=None,
            isMovie=True)

        self.assertEqual(
            [],
            list(self.test_obj.actors.all()))
        self.assertEqual(
            [],
            list(self.test_obj.writers.all()))
        self.assertEqual(
            [],
            list(self.test_obj.directors.all()))

    def test_file_is_movie(self):
        self.test_obj.file = self.movie_file

        expected = None
        actual = self.test_obj._cast_and_crew()

        self.assertEqual(expected, actual)
        self.mock_getCastData.assert_called_once_with(
            123,
            season=None,
            episode=None,
            isMovie=True)

        self.assertEqual(
            'Test_Actor',
            self.test_obj.actors.all()[0].name)
        self.assertEqual(
            'Test_Writer',
            self.test_obj.writers.all()[0].name)
        self.assertEqual(
            'Test_Director',
            self.test_obj.directors.all()[0].name)

    def test_path_for_tv(self):
        self.test_obj.path = self.tv_path

        expected = None
        actual = self.test_obj._cast_and_crew()

        self.assertEqual(expected, actual)
        self.mock_getCastData.assert_called_once_with(
            123,
            season=None,
            episode=None,
            isMovie=False)

        self.assertEqual(
            'Test_Actor',
            self.test_obj.actors.all()[0].name)
        self.assertEqual(
            'Test_Writer',
            self.test_obj.writers.all()[0].name)
        self.assertEqual(
            'Test_Director',
            self.test_obj.directors.all()[0].name)

    def test_file_is_tv(self):
        self.test_obj.file = self.tv_file

        expected = None
        actual = self.test_obj._cast_and_crew()

        self.assertEqual(expected, actual)
        self.mock_getCastData.assert_called_once_with(
            123,
            season=3,
            episode=5,
            isMovie=False)

        self.assertEqual(
            'Test_Actor',
            self.test_obj.actors.all()[0].name)
        self.assertEqual(
            'Test_Writer',
            self.test_obj.writers.all()[0].name)
        self.assertEqual(
            'Test_Director',
            self.test_obj.directors.all()[0].name)


class TestTVDBEpisodeInfo(TestCase):
    def setUp(self):
        getTVDBEpisodeInfo_patcher = mock.patch(
            'mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        self.fake_data = {'still_path': 'test_path',
                          'overview': 'test_overview',
                          'name': 'test_name'}
        self.tvdb_id = 123

        self.test_obj = PosterFile()

    def test_got_tvinfo(self):
        self.mock_getTVDBEpisodeInfo.return_value = self.fake_data

        expected = None
        actual = self.test_obj._tvdb_episode_info(self.tvdb_id)

        self.assertEqual(expected, actual)
        self.mock_getTVDBEpisodeInfo.assert_called_once_with(
            123,
            self.test_obj.season,
            self.test_obj.episode)
        self.assertEqual('test_path', self.test_obj.poster_url)
        self.assertEqual('test_overview', self.test_obj.extendedplot)
        self.assertEqual('test_name', self.test_obj.episodename)

    def test_no_tvinfo(self):
        self.mock_getTVDBEpisodeInfo.return_value = None

        expected = None
        actual = self.test_obj._tvdb_episode_info(self.tvdb_id)

        self.assertEqual(expected, actual)
        self.mock_getTVDBEpisodeInfo.assert_called_once_with(
            123,
            self.test_obj.season,
            self.test_obj.episode)
        self.assertEqual(None, self.test_obj.poster_url)
        self.assertEqual('', self.test_obj.extendedplot)
        self.assertEqual(None, self.test_obj.episodename)


class TestAssignTVDBInfo(TestCase):
    def setUp(self):
        searchTVDBByName_patcher = mock.patch(
            'mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        tvdb_episode_info_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._tvdb_episode_info')
        self.mock_tvdb_episode_info = tvdb_episode_info_patcher.start()
        self.addCleanup(tvdb_episode_info_patcher.stop)

        self.fake_data = {
            'results': [
                {'id': 123},
            ]
        }
        self.mock_searchTVDBByName.return_value = self.fake_data

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('new.file.mp4',
                                   self.movie_path)

        self.test_obj = PosterFile()

    def test_movie_file(self):
        self.test_obj.file = self.movie_file

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_tvdb_episode_info.called)

    def test_movie_path(self):
        self.test_obj.path = self.movie_path

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_tvdb_episode_info.called)

    def test_tv_path(self):
        self.test_obj.path = self.tv_path

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_tvdb_episode_info.called)

    def test_path_has_tvdb_id(self):
        self.tv_path.tvdb_id = 123
        self.test_obj.file = self.tv_file

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.mock_tvdb_episode_info.assert_called_once_with(123)

    def test_path_has_no_tvdb_id(self):
        self.test_obj.file = self.tv_file

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        self.assertEqual(expected, actual)
        self.assertEqual(self.tv_path.tvdb_id, 123)
        self.mock_searchTVDBByName.assert_called_once_with(
            self.tv_file.searchString())
        self.mock_tvdb_episode_info.assert_called_once_with(123)

    def test_badly_formatted_tvinfo(self):
        self.mock_searchTVDBByName.return_value = {}

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_tvdb_episode_info.called)


class TestPopulatePosterData(TestCase):
    def setUp(self):
        getIMDBData_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._getIMDBData')
        self.mock_getIMDBData = getIMDBData_patcher.start()
        self.addCleanup(getIMDBData_patcher.stop)

        download_poster_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._download_poster')
        self.mock_download_poster = download_poster_patcher.start()
        self.addCleanup(download_poster_patcher.stop)

        self.test_obj = PosterFile()

    def test_valid(self):
        expected = None
        actual = self.test_obj._populate_poster_data()

        self.assertEqual(expected, actual)
        self.mock_getIMDBData.assert_called_once_with()
        self.mock_download_poster.assert_called_once_with()


class TestDownloadPoster(TestCase):
    def setUp(self):
        saveImageToDisk_patcher = mock.patch(
            'mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        self.test_obj = PosterFile()
        self.test_obj.poster_url = '/test_poster_url'

    def test_missing_poster_url(self):
        self.test_obj.poster_url = None

        expected = None
        actual = self.test_obj._download_poster()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_saveImageToDisk.called)
        self.assertEqual(None, self.test_obj.image)

    def test_valid(self):
        expected = None
        actual = self.test_obj._download_poster()

        self.assertEqual(expected, actual)
        self.mock_saveImageToDisk.assert_called_once_with(
            self.test_obj.poster_url,
            self.test_obj.image)
        self.assertEqual('test_poster_url', self.test_obj.image)


class TestStorePlot(TestCase):
    def setUp(self):
        self.test_obj = PosterFile()

    def test_has_plot(self):
        test_data = {'Plot': 'test_plot'}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_plot', self.test_obj.plot)

    def test_has_overview(self):
        test_data = {'overview': 'test_overview'}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_overview', self.test_obj.plot)

    def test_has_multiple_results(self):
        test_data = {'results': [
            {'overview': 'test_results_overview'},
        ]}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_results_overview', self.test_obj.plot)

    def test_plot_undefined(self):
        test_data = {'Plot': 'undefined'}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual(None, self.test_obj.plot)


class TestStoreGenres(TestCase):
    def setUp(self):
        tvdbConfig_patcher = mock.patch(
            'mediaviewer.models.posterfile.tvdbConfig')
        self.mock_tvdbConfig = tvdbConfig_patcher.start()
        self.addCleanup(tvdbConfig_patcher.stop)

        self.mock_tvdbConfig.genres = {
            123: 'test_genre'}

        self.test_obj = PosterFile()
        self.test_obj.save()

    def test_has_results(self):
        imdb_data = {
            'results': [
                {'genre_ids': [123]},
            ],
        }

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        self.assertEqual(expected, actual)
        self.assertEqual('Test_Genre', self.test_obj.genres.all()[0].genre)

    def test_has_genre_ids(self):
        imdb_data = {'genre_ids': [123]}

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        self.assertEqual(expected, actual)
        self.assertEqual('Test_Genre', self.test_obj.genres.all()[0].genre)

    def test_has_genres(self):
        imdb_data = {'genres': [
            {'name': 'test_genre'},
        ]}

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        self.assertEqual(expected, actual)
        self.assertEqual('Test_Genre', self.test_obj.genres.all()[0].genre)


class TestStoreRating(TestCase):
    def setUp(self):
        self.test_obj = PosterFile()

    def test_has_imdb_rating(self):
        test_data = {
            'imdbRating': 'test_rating',
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_rating', self.test_obj.rating)

    def test_has_vote_average(self):
        test_data = {
            'vote_average': 'test_rating',
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_rating', self.test_obj.rating)

    def test_undefined(self):
        test_data = {
            'vote_average': 'undefined',
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual(None, self.test_obj.rating)


class TestStoreTagline(TestCase):
    def setUp(self):
        self.test_obj = PosterFile()

    def test_has_vote_average(self):
        test_data = {
            'tagline': 'test_tagline',
        }

        expected = None
        actual = self.test_obj._store_tagline(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_tagline', self.test_obj.tagline)

    def test_undefined(self):
        test_data = {
            'tagline': 'undefined',
        }

        expected = None
        actual = self.test_obj._store_tagline(test_data)

        self.assertEqual(expected, actual)
        self.assertEqual(None, self.test_obj.tagline)


@pytest.mark.django_db
class TestStoreExtendedInfo:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getExtendedInfo = mocker.patch(
            'mediaviewer.models.posterfile.getExtendedInfo')

        self.mock_store_rating = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_rating')

        self.mock_store_tagline = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_tagline')

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.test_obj = PosterFile()
        self.test_obj.tmdb_id = 123
        self.test_obj.file = self.tv_file

    def test_valid(self):
        expected = None
        actual = self.test_obj._store_extended_info()

        assert expected == actual
        self.mock_getExtendedInfo.assert_called_once_with(
            123,
            isMovie=False)
        self.mock_store_rating.assert_called_once_with(
            self.mock_getExtendedInfo.return_value)
        self.mock_store_tagline.assert_called_once_with(
            self.mock_getExtendedInfo.return_value)


class TestStoreRated:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_data = {'Rated': 'test_rated'}

        self.test_obj = PosterFile()

    def test_has_rated(self):
        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        assert expected == actual
        assert 'test_rated' == self.test_obj.rated

    def test_no_rated(self):
        self.test_data = {}

        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        assert expected == actual
        assert self.test_obj.rated is None

    def test_undefined(self):
        self.test_data = {'Rated': 'undefined'}

        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        assert expected == actual
        assert self.test_obj.rated is None
