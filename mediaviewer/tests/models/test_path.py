from django.test import TestCase
import mock

from mediaviewer.models.path import Path
from mediaviewer.models.posterfile import PosterFile

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

class TestHandleTVDB(TestCase):
    def setUp(self):
        searchTVDBByName_patcher = mock.patch('mediaviewer.models.path.searchTVDBByName')
        self.mock_searchTVDBByName = searchTVDBByName_patcher.start()
        self.addCleanup(searchTVDBByName_patcher.stop)

        saveImageToDisk_patcher = mock.patch('mediaviewer.models.path.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        assignDataToPoster_patcher = mock.patch('mediaviewer.models.path.assignDataToPoster')
        self.mock_assignDataToPoster = assignDataToPoster_patcher.start()
        self.addCleanup(assignDataToPoster_patcher.stop)

        tvdbConfig_patcher = mock.patch('mediaviewer.models.path.tvdbConfig')
        self.mock_tvdbConfig = tvdbConfig_patcher.start()
        self.mock_tvdbConfig.url = 'mock_url'
        self.mock_tvdbConfig.still_size = 'mock_still_size'
        self.addCleanup(tvdbConfig_patcher.stop)

        self.path = Path()
        self.path.defaultsearchstr = 'test str'

        self.poster = mock.create_autospec(PosterFile)

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
        saveImageToDisk_patcher = mock.patch('mediaviewer.models.path.saveImageToDisk')
        self.mock_saveImageToDisk = saveImageToDisk_patcher.start()
        self.addCleanup(saveImageToDisk_patcher.stop)

        getDataFromIMDBByPath_patcher = mock.patch('mediaviewer.models.path.getDataFromIMDBByPath')
        self.mock_getDataFromIMDBByPath = getDataFromIMDBByPath_patcher.start()
        self.addCleanup(getDataFromIMDBByPath_patcher.stop)

        assignDataToPoster_patcher = mock.patch('mediaviewer.models.path.assignDataToPoster')
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
