import mock
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


class TestAssignDataToPoster(TestCase):
    def setUp(self):
        genres_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile.genres')
        genres_patcher.start()
        self.addCleanup(genres_patcher.stop)
        actors_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile.actors')
        actors_patcher.start()
        self.addCleanup(actors_patcher.stop)
        writers_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile.writers')
        writers_patcher.start()
        self.addCleanup(writers_patcher.stop)
        directors_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile.directors')
        directors_patcher.start()
        self.addCleanup(directors_patcher.stop)

        genre_obj_patcher = mock.patch(
                'mediaviewer.models.posterfile.Genre.new')
        genre_obj_patcher.start()
        self.addCleanup(genre_obj_patcher.stop)

        actor_obj_patcher = mock.patch(
                'mediaviewer.models.posterfile.Actor.new')
        actor_obj_patcher.start()
        self.addCleanup(actor_obj_patcher.stop)

        writer_obj_patcher = mock.patch(
                'mediaviewer.models.posterfile.Writer.new')
        writer_obj_patcher.start()
        self.addCleanup(writer_obj_patcher.stop)

        director_obj_patcher = mock.patch(
                'mediaviewer.models.posterfile.Director.new')
        director_obj_patcher.start()
        self.addCleanup(director_obj_patcher.stop)

        getRating_patcher = mock.patch(
                'mediaviewer.models.posterfile.getRating')
        self.mock_getRating = getRating_patcher.start()
        self.addCleanup(getRating_patcher.stop)

        self.poster = PosterFile()
        self.poster.plot = None
        self.poster.rating = None
        self.poster.rated = None
        self.poster.extendedplot = None
        self.poster.tmdb_id = 1234

        self.ref_obj = mock.MagicMock(File)

    def test_all_data(self):
        data = sample_good_result

        self.poster._assignDataToPoster(data, sample_good_crew, self.ref_obj)

        self.assertEquals(self.poster.plot, data['overview'])
        self.assertEquals(self.poster.rating, self.mock_getRating.return_value)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, None)

        self.mock_getRating.assert_called_once_with(
                1234,
                isMovie=self.ref_obj.isMovie.return_value)


class TestNew(TestCase):
    def setUp(self):
        objects_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile.objects')
        self.mock_objects = objects_patcher.start()
        self.addCleanup(objects_patcher.stop)

        downloadPosterData_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile._downloadPosterData')
        self.mock_downloadPosterData = downloadPosterData_patcher.start()
        self.addCleanup(downloadPosterData_patcher.stop)

        populate_poster_data_patcher = mock.patch(
            'mediaviewer.models.posterfile.PosterFile._populate_poster_data')
        self.mock_populate_poster_data = populate_poster_data_patcher.start()
        self.addCleanup(populate_poster_data_patcher.stop)

        self.path = Path.new('local.path',
                             'remote.path',
                             is_movie=False)
        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
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


class TestMovieDownloadPosterData(TestCase):
    def setUp(self):
        getDataFromIMDB_patcher = mock.patch(
                'mediaviewer.models.posterfile.getDataFromIMDB')
        self.mock_getDataFromIMDB = getDataFromIMDB_patcher.start()
        self.mock_getDataFromIMDB.return_value = sample_good_result
        self.addCleanup(getDataFromIMDB_patcher.stop)

        getCastData_patcher = mock.patch(
                'mediaviewer.models.posterfile.getCastData')
        self.mock_getCastData = getCastData_patcher.start()
        self.mock_getCastData.return_value = sample_good_crew
        self.addCleanup(getCastData_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch(
                'mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        searchTVDBByName_patcher = mock.patch(
                'mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        getTVDBEpisodeInfo_patcher = mock.patch(
                'mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        saveImageToDisk_patcher = mock.patch(
                'mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch(
                'mediaviewer.models.posterfile.tvdbConfig')
        self.mock_tvdbConfig = tvdbConfig_patcher.start()
        self.mock_tvdbConfig.url = 'mock_url'
        self.mock_tvdbConfig.still_size = 'mock_still_size'
        self.addCleanup(tvdbConfig_patcher.stop)

        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
                                   is_movie=True)

        self.movie_file = File.new('movie.file', self.movie_path)

        self.poster = PosterFile()
        self.poster.file = self.movie_file

    def test_path_is_movie(self):
        self.poster.file = None
        self.poster.path = self.movie_path

        self.assertRaises(ValueError,
                          self.poster._downloadPosterData)

    def test_(self):
        self.poster._downloadPosterData()
        self.mock_getDataFromIMDB.assert_called_once_with(self.movie_file)
        self.assertFalse(self.mock_getDataFromIMDBByPath.called)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_getTVDBEpisodeInfo.called)
        self.mock_saveImageToDisk.assert_called_once_with(u'/zxcvzxcv.jpg',
                                                          u'zxcvzxcv.jpg')
        self.mock_assignDataToPoster.assert_any_call(
                sample_good_result,
                sample_good_crew,
                self.movie_file)


class TestTVPathDownloadPosterData(TestCase):
    def setUp(self):
        getDataFromIMDB_patcher = mock.patch(
                'mediaviewer.models.posterfile.getDataFromIMDB')
        self.mock_getDataFromIMDB = getDataFromIMDB_patcher.start()
        self.addCleanup(getDataFromIMDB_patcher.stop)

        getCastData_patcher = mock.patch(
                'mediaviewer.models.posterfile.getCastData')
        self.mock_getCastData = getCastData_patcher.start()
        self.mock_getCastData.return_value = sample_good_crew
        self.addCleanup(getCastData_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch(
                'mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.mock_getDataFromIMDBByPath.return_value = sample_good_result
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        searchTVDBByName_patcher = mock.patch(
                'mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        getTVDBEpisodeInfo_patcher = mock.patch(
                'mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        saveImageToDisk_patcher = mock.patch(
                'mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch(
                'mediaviewer.models.posterfile.tvdbConfig')
        self.mock_tvdbConfig = tvdbConfig_patcher.start()
        self.mock_tvdbConfig.url = 'mock_url'
        self.mock_tvdbConfig.still_size = 'mock_still_size'
        self.addCleanup(tvdbConfig_patcher.stop)

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)

        self.poster = PosterFile()
        self.poster.path = self.tv_path

    def test_(self):
        self.tv_path.tvdb_id = None

        self.poster._downloadPosterData()
        self.mock_getDataFromIMDBByPath(self.tv_path)
        self.assertFalse(self.mock_getDataFromIMDB.called)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_getTVDBEpisodeInfo.called)
        self.mock_saveImageToDisk.assert_called_once_with(
                u'/path/to/image.jpg',
                'image.jpg')
        self.mock_assignDataToPoster.assert_any_call(
                sample_good_result,
                sample_good_crew,
                self.tv_path)


class TestTVFileDownloadPosterData(TestCase):
    def setUp(self):
        getDataFromIMDB_patcher = mock.patch(
                'mediaviewer.models.posterfile.getDataFromIMDB')
        self.mock_getDataFromIMDB = getDataFromIMDB_patcher.start()
        self.mock_getDataFromIMDB.return_value = sample_good_result
        self.addCleanup(getDataFromIMDB_patcher.stop)

        getCastData_patcher = mock.patch(
                'mediaviewer.models.posterfile.getCastData')
        self.mock_getCastData = getCastData_patcher.start()
        self.mock_getCastData.return_value = sample_good_crew
        self.addCleanup(getCastData_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch(
                'mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        searchTVDBByName_patcher = mock.patch(
                'mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        getTVDBEpisodeInfo_patcher = mock.patch(
                'mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        saveImageToDisk_patcher = mock.patch(
                'mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch(
                'mediaviewer.models.posterfile.tvdbConfig')
        self.mock_tvdbConfig = tvdbConfig_patcher.start()
        self.mock_tvdbConfig.url = 'mock_url'
        self.mock_tvdbConfig.still_size = 'mock_still_size'
        self.addCleanup(tvdbConfig_patcher.stop)

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.poster = PosterFile()
        self.poster.file = self.tv_file

    def test_no_tvinfo(self):
        self.mock_searchTVDBByName.return_value = {}

        self.poster._downloadPosterData()
        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.assertFalse(self.mock_getTVDBEpisodeInfo.called)
        self.mock_saveImageToDisk.assert_called_once_with(
                u'/path/to/image.jpg',
                'image.jpg')
        self.mock_assignDataToPoster.assert_any_call(
                sample_good_result,
                sample_good_crew,
                self.tv_file)

    def test_bad_result(self):
        self.mock_searchTVDBByName.return_value = sample_bad_result

        self.poster._downloadPosterData()
        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.assertFalse(self.mock_getTVDBEpisodeInfo.called)
        self.mock_saveImageToDisk.assert_called_once_with(u'/zxcvzxcv.jpg',
                                                          u'zxcvzxcv.jpg')
        self.mock_assignDataToPoster.assert_any_call(
                sample_good_result,
                sample_good_crew,
                self.tv_file)

    def test_no_poster_data(self):
        mock_result = {u'page': 1,
                       u'results': [{u'backdrop_path': u'/asdfasdf.jpg',
                                     u'first_air_date': u'2016-09-30',
                                     u'genre_ids': [18, 10765],
                                     u'id': 12345,
                                     u'name': u"show name",
                                     u'origin_country': [u'US'],
                                     u'original_language': u'en',
                                     u'original_name': u"show name",
                                     u'overview': u'show description',
                                     u'popularity': 4.278642,
                                     u'vote_average': 6.81,
                                     u'vote_count': 41}],
                       u'total_pages': 1,
                       u'total_results': 1}
        self.mock_searchTVDBByName.return_value = mock_result

        mock_tv_info_result = {'still_path': u'/path/to/image.jpg',
                               'overview': 'tv info overview',
                               'name': 'episode name'}
        self.mock_getTVDBEpisodeInfo.return_value = mock_tv_info_result

        self.poster._downloadPosterData()

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.mock_getTVDBEpisodeInfo.assert_called_once_with(12345, 3, 5)
        self.mock_saveImageToDisk.assert_called_once_with(
                u'/path/to/image.jpg',
                'image.jpg')
        self.mock_assignDataToPoster.assert_called_once_with(
                sample_good_result,
                sample_good_crew,
                self.tv_file)
        self.assertEqual(self.poster.file.path.tvdb_id, 12345)

    def test_response_with_poster_data(self):
        mock_result = {u'page': 1,
                       u'results': [{u'backdrop_path': u'/asdfasdf.jpg',
                                     u'first_air_date': u'2016-09-30',
                                     u'genre_ids': [18, 10765],
                                     u'id': 12345,
                                     u'name': u"show name",
                                     u'origin_country': [u'US'],
                                     u'original_language': u'en',
                                     u'original_name': u"show name",
                                     u'overview': u'show description',
                                     u'popularity': 4.278642,
                                     u'vote_average': 6.81,
                                     u'vote_count': 41}],
                       u'total_pages': 1,
                       u'total_results': 1}
        self.mock_searchTVDBByName.return_value = mock_result
        mock_tv_info_result = {'still_path': u'/path/to/image.jpg',
                               'overview': 'tv info overview',
                               'name': 'episode name'}
        self.mock_getTVDBEpisodeInfo.return_value = mock_tv_info_result

        self.poster._downloadPosterData()

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.mock_getTVDBEpisodeInfo.assert_called_once_with(12345, 3, 5)
        self.mock_saveImageToDisk.assert_called_once_with(
                u'/path/to/image.jpg',
                'image.jpg')
        self.mock_assignDataToPoster.assert_called_once_with(
                sample_good_result,
                sample_good_crew,
                self.tv_file)
        self.assertEqual(self.poster.file.path.tvdb_id, 12345)
        self.assertEqual(self.poster.image, 'image.jpg')


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

        store_rating_patcher = mock.patch(
                'mediaviewer.models.posterfile.PosterFile._store_rating')
        self.mock_store_rating = store_rating_patcher.start()
        self.addCleanup(store_rating_patcher.stop)

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

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
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
        self.mock_store_rating.assert_called_once_with()
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

        self.mock_store_rating.assert_called_once_with()
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

        self.mock_store_rating.assert_called_once_with()
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
        self.assertFalse(self.mock_store_rating.called)
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
        self.assertFalse(self.mock_store_rating.called)
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
        self.assertFalse(self.mock_store_rating.called)
        self.assertFalse(self.mock_store_plot.called)
        self.assertFalse(self.mock_store_genres.called)
        self.assertFalse(self.mock_store_rated.called)


class TestCastAndCrew(TestCase):
    def setUp(self):
        getCastData_patcher = mock.patch(
                'mediaviewer.models.posterfile.getCastData')
        self.mock_getCastData = getCastData_patcher.start()
        self.addCleanup(getCastData_patcher.stop)

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
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

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
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
        self.test_obj.poster_url = 'test_poster_url'
        self.test_obj.image = 'test_image'

    def test_missing_poster_url(self):
        self.test_obj.poster_url = None

        expected = None
        actual = self.test_obj._download_poster()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_saveImageToDisk.called)

    def test_missing_image(self):
        self.test_obj.image = None

        expected = None
        actual = self.test_obj._download_poster()

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_saveImageToDisk.called)

    def test_valid(self):
        expected = None
        actual = self.test_obj._download_poster()

        self.assertEqual(expected, actual)
        self.mock_saveImageToDisk.assert_called_once_with(
                self.test_obj.poster_url,
                self.test_obj.image)


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
        # new_patcher = mock.patch(
                # 'mediaviewer.models.posterfile.Genre.new')
        # self.mock_new = new_patcher.start()
        # self.addCleanup(new_patcher.stop)

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
        getRating_patcher = mock.patch(
                'mediaviewer.models.posterfile.getRating')
        self.mock_getRating = getRating_patcher.start()
        self.addCleanup(getRating_patcher.stop)

        self.mock_getRating.return_value = 'test_rating'

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.test_obj = PosterFile()
        self.test_obj.tmdb_id = 123
        self.test_obj.file = self.tv_file

    def test_has_rating(self):
        expected = None
        actual = self.test_obj._store_rating()

        self.assertEqual(expected, actual)
        self.mock_getRating.assert_called_once_with(
                123,
                isMovie=False)
        self.assertEqual('test_rating', self.test_obj.rating)

    def test_no_rating(self):
        self.mock_getRating.return_value = None

        expected = None
        actual = self.test_obj._store_rating()

        self.assertEqual(expected, actual)
        self.mock_getRating.assert_called_once_with(
                123,
                isMovie=False)
        self.assertEqual(None, self.test_obj.rating)

    def test_undefined(self):
        self.mock_getRating.return_value = 'undefined'

        expected = None
        actual = self.test_obj._store_rating()

        self.assertEqual(expected, actual)
        self.mock_getRating.assert_called_once_with(
                123,
                isMovie=False)
        self.assertEqual(None, self.test_obj.rating)


class TestStoreRated(TestCase):
    def setUp(self):
        self.test_data = {'Rated': 'test_rated'}

        self.test_obj = PosterFile()

    def test_has_rated(self):
        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        self.assertEqual(expected, actual)
        self.assertEqual('test_rated', self.test_obj.rated)

    def test_no_rated(self):
        self.test_data = {}

        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        self.assertEqual(expected, actual)
        self.assertEqual(None, self.test_obj.rated)

    def test_undefined(self):
        self.test_data = {'Rated': 'undefined'}

        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        self.assertEqual(expected, actual)
        self.assertEqual(None, self.test_obj.rated)
