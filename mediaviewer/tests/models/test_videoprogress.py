import mock

from django.test import TestCase
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

from django.contrib.auth.models import User

class TestDestroy(TestCase):
    def setUp(self):
        self.clearLastWatchedMessage_patcher = mock.patch('mediaviewer.models.videoprogress.Message.clearLastWatchedMessage')
        self.mock_clearLastWatchedMessage = self.clearLastWatchedMessage_patcher.start()

        self.delete_patcher = mock.patch('mediaviewer.models.videoprogress.VideoProgress.delete')
        self.mock_delete = self.delete_patcher.start()

        self.user = User()
        self.user.save()

        self.path = Path.new('local_path',
                             'remote_path',
                             False)

        self.filename = 'test_filename'

        self.file = File.new(self.filename,
                             self.path)

        self.vp = VideoProgress.new(self.user,
                                    self.filename,
                                    'hashed_filename',
                                    100,
                                    self.file)

    def tearDown(self):
        self.clearLastWatchedMessage_patcher.stop()
        self.delete_patcher.stop()

    def test_no_videoprogress(self):
        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'non-existent_filename_hash')

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_clearLastWatchedMessage.called)
        self.assertFalse(self.mock_delete.called)

    def test_no_next(self):
        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'hashed_filename')

        self.assertEqual(expected, actual)
        self.mock_clearLastWatchedMessage.assert_called_once_with(self.user)
        self.mock_delete.assert_called_once_with()

    def test_with_next_file(self):
        File.new('test_filename2',
                 self.path)

        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'hashed_filename')

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_clearLastWatchedMessage.called)
        self.mock_delete.assert_called_once_with()

