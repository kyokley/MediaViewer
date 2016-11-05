from django.test import TestCase
import mock

from mediaviewer.models.path import Path
from mediaviewer.models.posterfile import PosterFile

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
