from django.test import TestCase

from django.contrib.auth.models import User
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from datetime import datetime, timedelta

import pytz
import mock

@mock.patch('mediaviewer.models.downloadtoken.DownloadToken.save')
class TestDownloadToken(TestCase):
    def setUp(self):
        #self.user = mock.create_autospec(User)
        self.user = User()

        self.path = Path()
        self.path.localpathstr = '/path/to/file'
        self.path.is_movie = False

        #self.file = mock.create_autospec(File)
        self.file = File()
        self.file.filename = 'some file'
        self.file.path = self.path

    def test_new(self, mock_save):
        dt = DownloadToken.new(self.user,
                               self.file)

        self.assertEqual(dt.filename, 'some file')
        self.assertEqual(dt.path, '/path/to/file')
        self.assertEqual(dt.ismovie, False)
        self.assertEqual(dt.displayname, 'some file')
        self.assertEqual(dt.file, self.file)
        mock_save.assert_called_once_with()

    def test_isvalid(self, mock_save):
        dt = DownloadToken.new(self.user,
                               self.file)
        self.assertTrue(dt.isvalid)

    def test_isNotValid(self, mock_save):
        dt = DownloadToken.new(self.user,
                               self.file,
                               datecreated=datetime.now(pytz.timezone('US/Central')) - timedelta(hours=4))
        self.assertFalse(dt.isvalid)
