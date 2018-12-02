from django.test import TestCase

from django.contrib.auth.models import User
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mysite.settings import (MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS,
                             TOKEN_VALIDITY_LENGTH,
                             TIME_ZONE)
from datetime import datetime, timedelta

import pytz
import mock

class TestDownloadToken(TestCase):
    def setUp(self):
        self.save_patcher = mock.patch('mediaviewer.models.downloadtoken.DownloadToken.save')
        self.mock_save = self.save_patcher.start()

        self.objects_patcher = mock.patch('mediaviewer.models.downloadtoken.DownloadToken.objects')
        self.mock_objects = self.objects_patcher.start()

        self.createLastWatchedMessage_patcher = mock.patch('mediaviewer.models.downloadtoken.Message.createLastWatchedMessage')
        self.mock_createLastWatchedMessage = self.createLastWatchedMessage_patcher.start()

        self.user = User()
        self.user.settings = lambda : mock.MagicMock()

        self.path = Path()
        self.path.localpathstr = '/path/to/file'
        self.path.is_movie = False

        self.file = File()
        self.file.filename = 'some file'
        self.file.path = self.path

    def tearDown(self):
        self.save_patcher.stop()
        self.objects_patcher.stop()
        self.createLastWatchedMessage_patcher.stop()

    def test_new(self):
        self.mock_objects.count.return_value = MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS + 1
        mock_ordered_query = mock.MagicMock()
        old_token = mock.create_autospec(DownloadToken)
        mock_ordered_query.first.return_value = old_token
        self.mock_objects.order_by.return_value = mock_ordered_query
        dt = DownloadToken.new(self.user,
                               self.file)


        self.assertEqual(dt.filename, 'some file')
        self.assertEqual(dt.path, '/path/to/file')
        self.assertEqual(dt.ismovie, False)
        self.assertEqual(dt.displayname, 'some file')
        self.assertEqual(dt.file, self.file)
        self.mock_save.assert_called_once_with()
        self.assertTrue(self.mock_objects.count.called)
        self.assertTrue(old_token.delete.called)
        self.mock_createLastWatchedMessage.assert_called_once_with(self.user, self.file)

    def test_isvalid(self):
        dt = DownloadToken.new(self.user,
                               self.file)
        self.assertTrue(dt.isvalid)

    def test_isNotValid(self):
        dt = DownloadToken.new(self.user,
                               self.file,
                               datecreated=datetime.now(pytz.timezone(TIME_ZONE)) - timedelta(hours=TOKEN_VALIDITY_LENGTH + 1))
        self.assertFalse(dt.isvalid)
