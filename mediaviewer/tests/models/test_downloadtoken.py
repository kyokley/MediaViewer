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

@mock.patch('mediaviewer.models.downloadtoken.DownloadToken.save')
class TestDownloadToken(TestCase):
    def setUp(self):
        self.user = User()

        self.path = Path()
        self.path.localpathstr = '/path/to/file'
        self.path.is_movie = False

        self.file = File()
        self.file.filename = 'some file'
        self.file.path = self.path

    @mock.patch('mediaviewer.models.downloadtoken.DownloadToken.objects')
    def test_new(self, mock_objects, mock_save):
        mock_objects.count.return_value = MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS + 1
        mock_ordered_query = mock.MagicMock()
        old_token = mock.create_autospec(DownloadToken)
        mock_ordered_query.first.return_value = old_token
        mock_objects.order_by.return_value = mock_ordered_query
        dt = DownloadToken.new(self.user,
                               self.file)


        self.assertEqual(dt.filename, 'some file')
        self.assertEqual(dt.path, '/path/to/file')
        self.assertEqual(dt.ismovie, False)
        self.assertEqual(dt.displayname, 'some file')
        self.assertEqual(dt.file, self.file)
        mock_save.assert_called_once_with()
        self.assertTrue(mock_objects.count.called)
        self.assertTrue(old_token.delete.called)

    def test_isvalid(self, mock_save):
        dt = DownloadToken.new(self.user,
                               self.file)
        self.assertTrue(dt.isvalid)

    def test_isNotValid(self, mock_save):
        dt = DownloadToken.new(self.user,
                               self.file,
                               datecreated=datetime.now(pytz.timezone(TIME_ZONE)) - timedelta(hours=TOKEN_VALIDITY_LENGTH + 1))
        self.assertFalse(dt.isvalid)
