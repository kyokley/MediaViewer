import mock
from django.test import TestCase

from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

class TestAssignDataToPoster(TestCase):
    def setUp(self):
        genres_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.genres', mock.MagicMock())
        genres_patcher.start()
        self.addCleanup(genres_patcher.stop)
        actors_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.actors', mock.MagicMock())
        actors_patcher.start()
        self.addCleanup(actors_patcher.stop)
        writers_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.writers', mock.MagicMock())
        writers_patcher.start()
        self.addCleanup(writers_patcher.stop)
        directors_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.directors', mock.MagicMock())
        directors_patcher.start()
        self.addCleanup(directors_patcher.stop)

        genre_obj_patcher = mock.patch('mediaviewer.models.posterfile.Genre.new', mock.MagicMock(side_effect=lambda x: x))
        genre_obj_patcher.start()
        self.addCleanup(genre_obj_patcher.stop)

        actor_obj_patcher = mock.patch('mediaviewer.models.posterfile.Actor.new', mock.MagicMock(side_effect=lambda x: x))
        actor_obj_patcher.start()
        self.addCleanup(actor_obj_patcher.stop)

        writer_obj_patcher = mock.patch('mediaviewer.models.posterfile.Writer.new', mock.MagicMock(side_effect=lambda x: x))
        writer_obj_patcher.start()
        self.addCleanup(writer_obj_patcher.stop)

        director_obj_patcher = mock.patch('mediaviewer.models.posterfile.Director.new', mock.MagicMock(side_effect=lambda x: x))
        director_obj_patcher.start()
        self.addCleanup(director_obj_patcher.stop)

        self.poster = PosterFile()
        self.poster.plot = None
        self.poster.rating = None
        self.poster.rated = None
        self.poster.extendedplot = None

    def test_all_data(self):
        data = {'Plot': 'plot',
                'Genre': 'Action, Drama, Crime',
                'Actors': 'Meridith Steele, Margy Marks, Merna Rutledge, Krissy Cole, Cammie Howell',
                'Writer': 'Eleonore Carter, Kym Hodge',
                'Director': 'Neda English, Gwyn Carson, Alica Ellis',
                'imdbRating': 'imdb_rating',
                'Rated': 'rated',
                }

        self.poster._assignDataToPoster(data)

        self.assertEquals(self.poster.plot, 'plot')
        self.poster.genres.add.assert_any_call('Action')
        self.poster.genres.add.assert_any_call('Drama')
        self.poster.genres.add.assert_any_call('Crime')
        self.poster.actors.add.assert_any_call('Meridith Steele')
        self.poster.actors.add.assert_any_call('Margy Marks')
        self.poster.actors.add.assert_any_call('Merna Rutledge')
        self.poster.actors.add.assert_any_call('Krissy Cole')
        self.poster.actors.add.assert_any_call('Cammie Howell')
        self.poster.writers.add.assert_any_call('Eleonore Carter')
        self.poster.writers.add.assert_any_call('Kym Hodge')
        self.poster.directors.add.assert_any_call('Neda English')
        self.poster.directors.add.assert_any_call('Gwyn Carson')
        self.poster.directors.add.assert_any_call('Alica Ellis')
        self.assertEquals(self.poster.rating, 'imdb_rating')
        self.assertEquals(self.poster.rated, 'rated')
        self.assertEquals(self.poster.extendedplot, None)

    def test_onlyExtendedPlot(self):
        data = {'Plot': 'plot',
                'Genre': 'genre',
                'Actors': 'actors',
                'Writer': 'writer',
                'Director': 'director',
                'imdbRating': 'imdb_rating',
                'Rated': 'rated',
                }

        self.poster._assignDataToPoster(data, onlyExtendedPlot=True)
        self.assertEquals(self.poster.plot, None)
        self.assertFalse(self.poster.genres.add.called)
        self.assertFalse(self.poster.actors.add.called)
        self.assertFalse(self.poster.writers.add.called)
        self.assertFalse(self.poster.directors.add.called)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, 'plot')

    def test_undefined(self):
        data = {'Plot': 'undefined',
                'Genre': 'undefined',
                'Actors': 'undefined',
                'Writer': 'undefined',
                'Director': 'undefined',
                'imdbRating': 'undefined',
                'Rated': 'undefined',
                }

        self.poster._assignDataToPoster(data, onlyExtendedPlot=False)
        self.assertEquals(self.poster.plot, None)
        self.assertFalse(self.poster.genres.add.called)
        self.assertFalse(self.poster.actors.add.called)
        self.assertFalse(self.poster.writers.add.called)
        self.assertFalse(self.poster.directors.add.called)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, None)

    def test_undefined_onlyExtendedPlot(self):
        data = {'Plot': 'undefined',
                'Genre': 'undefined',
                'Actors': 'undefined',
                'Writer': 'undefined',
                'Director': 'undefined',
                'imdbRating': 'undefined',
                'Rated': 'undefined',
                }

        self.poster._assignDataToPoster(data, onlyExtendedPlot=True)
        self.assertEquals(self.poster.plot, None)
        self.assertFalse(self.poster.genres.add.called)
        self.assertFalse(self.poster.actors.add.called)
        self.assertFalse(self.poster.writers.add.called)
        self.assertFalse(self.poster.directors.add.called)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, None)

class TestNew(TestCase):
    def setUp(self):
        objects_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.objects')
        self.mock_objects = objects_patcher.start()
        self.addCleanup(objects_patcher.stop)

        downloadPosterData_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile._downloadPosterData')
        self.mock_downloadPosterData = downloadPosterData_patcher.start()
        self.addCleanup(downloadPosterData_patcher.stop)

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
        self.mock_downloadPosterData.assert_called_once_with()

    def test_path(self):
        new_obj = PosterFile.new(path=self.path)

        self.assertEqual(new_obj.file, None)
        self.assertEqual(new_obj.path, self.path)
        self.mock_downloadPosterData.assert_called_once_with()

    def test_existing_for_file(self):
        self.mock_objects.filter.return_value.first.return_value = 'existing_obj'

        existing = PosterFile.new(file=self.file)
        self.assertEqual(existing, 'existing_obj')
        self.assertFalse(self.mock_downloadPosterData.called)

    def test_existing_for_path(self):
        self.mock_objects.filter.return_value.first.return_value = 'existing_obj'

        existing = PosterFile.new(path=self.path)
        self.assertEqual(existing, 'existing_obj')
        self.assertFalse(self.mock_downloadPosterData.called)

sample_good_result = {u'page': 1,
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
                                    u'poster_path': u'/zxcvzxcv.jpg',
                                    u'vote_average': 6.81,
                                    u'vote_count': 41}],
                      u'total_pages': 1,
                      u'total_results': 1}

sample_bad_result = {u'page': 1,
                     u'results': [],
                     u'total_pages': 1,
                     u'total_results': 0}

sample_imdb_result = {u'Actors': u'Actors',
                      u'Awards': u'N/A',
                      u'Country': u'USA',
                      u'Director': u'N/A',
                      u'Genre': u'Action, Crime, Drama',
                      u'Language': u'English',
                      u'Metascore': u'N/A',
                      u'Plot': u"plot",
                      u'Poster': u'/path/to/image.jpg',
                      u'Rated': u'TV-14',
                      u'Released': u'23 Jun 2016',
                      u'Response': u'True',
                      u'Runtime': u'60 min',
                      u'Title': u'Show title',
                      u'Type': u'series',
                      u'Writer': u'writers',
                      u'Year': u'2016\u2013',
                      u'imdbID': u'tt123456',
                      u'imdbRating': u'7.4',
                      u'imdbVotes': u'2,022',
                      u'totalSeasons': u'1',
                      'url': u'/path/to/omdbapi'}

class TestMovieDownloadPosterData(TestCase):
    def setUp(self):
        getDataFromIMDB_patcher = mock.patch('mediaviewer.models.posterfile.getDataFromIMDB')
        self.mock_getDataFromIMDB = getDataFromIMDB_patcher.start()
        self.mock_getDataFromIMDB.return_value = sample_imdb_result
        self.addCleanup(getDataFromIMDB_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch('mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        searchTVDBByName_patcher = mock.patch('mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        getTVDBEpisodeInfo_patcher = mock.patch('mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        saveImageToDisk_patcher = mock.patch('mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch('mediaviewer.models.posterfile.tvdbConfig')
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
        self.mock_getDataFromIMDB.assert_called_once_with(self.movie_file, useExtendedPlot=True)
        self.assertFalse(self.mock_getDataFromIMDBByPath.called)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_getTVDBEpisodeInfo.called)
        self.mock_saveImageToDisk.assert_called_once_with(u'/path/to/image.jpg',
                                                          u'image.jpg')
        self.mock_assignDataToPoster.assert_any_call(sample_imdb_result)
        self.mock_assignDataToPoster.assert_any_call(sample_imdb_result, onlyExtendedPlot=True)

class TestTVPathDownloadPosterData(TestCase):
    def setUp(self):
        getDataFromIMDB_patcher = mock.patch('mediaviewer.models.posterfile.getDataFromIMDB')
        self.mock_getDataFromIMDB = getDataFromIMDB_patcher.start()
        self.addCleanup(getDataFromIMDB_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch('mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.mock_getDataFromIMDBByPath.return_value = sample_imdb_result
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        searchTVDBByName_patcher = mock.patch('mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        getTVDBEpisodeInfo_patcher = mock.patch('mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        saveImageToDisk_patcher = mock.patch('mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch('mediaviewer.models.posterfile.tvdbConfig')
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
        self.mock_getDataFromIMDBByPath(self.tv_path, useExtendedPlot=True)
        self.assertFalse(self.mock_getDataFromIMDB.called)
        self.assertFalse(self.mock_searchTVDBByName.called)
        self.assertFalse(self.mock_getTVDBEpisodeInfo.called)
        self.mock_saveImageToDisk.assert_called_once_with(u'/path/to/image.jpg',
                                                          u'image.jpg')
        self.mock_assignDataToPoster.assert_any_call(sample_imdb_result)
        self.mock_assignDataToPoster.assert_any_call(sample_imdb_result, onlyExtendedPlot=True)

class TestTVDownloadPosterData(TestCase):
    def setUp(self):
        searchTVDBByName_patcher = mock.patch('mediaviewer.models.posterfile.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        getTVDBEpisodeInfo_patcher = mock.patch('mediaviewer.models.posterfile.getTVDBEpisodeInfo')
        self.mock_getTVDBEpisodeInfo = getTVDBEpisodeInfo_patcher.start()
        self.addCleanup(getTVDBEpisodeInfo_patcher.stop)

        saveImageToDisk_patcher = mock.patch('mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch('mediaviewer.models.posterfile.tvdbConfig')
        self.mock_tvdbConfig = tvdbConfig_patcher.start()
        self.mock_tvdbConfig.url = 'mock_url'
        self.mock_tvdbConfig.still_size = 'mock_still_size'
        self.addCleanup(tvdbConfig_patcher.stop)

        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)

        self.poster = PosterFile()

    def test_no_tvinfo(self):
        self.mock_searchTVDBByName.return_value = {}
        self.path._handleDataFromTVDB(self.poster)

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.assertFalse(self.mock_saveImageToDisk.called)
        self.mock_assignDataToPoster.assert_called_once_with({},
                                                             self.poster,
                                                             foundNone=True)

    def test_bad_result(self):
        self.mock_searchTVDBByName.return_value = sample_bad_result
        self.path._handleDataFromTVDB(self.poster)

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.assertFalse(self.mock_saveImageToDisk.called)
        self.mock_assignDataToPoster.assert_called_once_with({},
                                                             self.poster,
                                                             foundNone=True)

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

        self.path._handleDataFromTVDB(self.poster)

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.assertFalse(self.mock_saveImageToDisk.called)
        self.mock_assignDataToPoster.assert_called_once_with({u'backdrop_path': u'/asdfasdf.jpg',
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
                                                              u'vote_count': 41},
                                                             self.poster,
                                                             foundNone=False)
        self.assertEqual(self.path.tvdb_id, 12345)

    def test_response_with_poster_data(self):
        self.mock_searchTVDBByName.return_value = sample_good_result

        self.path._handleDataFromTVDB(self.poster)

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.mock_saveImageToDisk.assert_called_once_with('mock_url/mock_still_size/zxcvzxcv.jpg',
                                                          'zxcvzxcv.jpg')
        self.mock_assignDataToPoster.assert_called_once_with({u'backdrop_path': u'/asdfasdf.jpg',
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
                                                              u'poster_path': u'/zxcvzxcv.jpg',
                                                              u'vote_count': 41},
                                                             self.poster,
                                                             foundNone=False)
        self.assertEqual(self.path.tvdb_id, 12345)
        self.assertEqual(self.poster.image, 'zxcvzxcv.jpg')

class TestHandleIMDB(TestCase):
    def setUp(self):
        saveImageToDisk_patcher = mock.patch('mediaviewer.models.posterfile.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch('mediaviewer.models.posterfile.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        assignDataToPoster_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile._assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        self.path = Path()
        self.path.defaultsearchstr = 'test str'

        self.poster = mock.create_autospec(PosterFile)

    def test_(self):
        mock_data = {'Poster': '/path/to/image.jpg'}

        self.path._handleDataFromIMDB(mock_data, self.poster)

        self.mock_saveImageToDisk.assert_called_once_with('/path/to/image.jpg', 'image.jpg')
        self.assertEqual(self.poster.image, 'image.jpg')
        self.mock_assignDataToPoster.assert_any_call(mock_data, self.poster)
        self.mock_getDataFromIMDBByPath.assert_called_once_with(self.path,
                                                                useExtendedPlot=True)
        self.mock_assignDataToPoster.assert_any_call(self.mock_getDataFromIMDBByPath.return_value, self.poster, onlyExtendedPlot=True)
