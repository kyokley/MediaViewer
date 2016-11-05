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

    def test_no_poster_data(self):
        self.mock_searchTVDBByName.return_value = sample_bad_result
        self.path._handleDataFromTVDB(self.poster)

        self.mock_searchTVDBByName.assert_called_once_with('test str')
        self.assertFalse(self.mock_saveImageToDisk.called)
        self.mock_assignDataToPoster.assert_called_once_with({},
                                                             self.poster,
                                                             foundNone=True)
