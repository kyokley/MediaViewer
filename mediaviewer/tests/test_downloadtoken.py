from django.test import TestCase

from django.contrib.auth.models import User
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File

import mock

@mock.patch('mediaviewer.models.downloadtoken.DownloadToken.save')
class TestNew(TestCase):
    def setUp(self):
        self.user = mock.create_autospec(User)

        self.file = mock.create_autospec(File)
        self.file.filename = 'some file'
        self.file.path.localpathstr = '/path/to/file'

    def test_new(self, mock_save):
        pass
