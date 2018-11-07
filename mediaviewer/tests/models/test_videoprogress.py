import mock

from django.test import TestCase
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

from mediaviewer.tests import helpers


class TestDestroy(TestCase):
    def setUp(self):
        clearLastWatchedMessage_patcher = mock.patch(
            'mediaviewer.models.videoprogress.Message.clearLastWatchedMessage')
        self.mock_clearLastWatchedMessage = (
                clearLastWatchedMessage_patcher.start())
        self.addCleanup(clearLastWatchedMessage_patcher.stop)

        self.user = helpers.create_user()

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

    def test_no_videoprogress(self):
        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'non-existent_filename_hash')

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_clearLastWatchedMessage.called)
        self.assertEqual(
                [self.vp],
                list(VideoProgress.objects.all()))

    def test_no_next(self):
        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'hashed_filename')

        self.assertEqual(expected, actual)
        self.mock_clearLastWatchedMessage.assert_called_once_with(self.user)
        self.assertFalse(VideoProgress.objects.exists())

    def test_with_next_file(self):
        File.new('test_filename2',
                 self.path)

        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'hashed_filename')

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_clearLastWatchedMessage.called)
        self.assertFalse(VideoProgress.objects.exists())


class TestCreateOrUpdate(TestCase):
    def setUp(self):
        self.user = helpers.create_user()
        self.user2 = helpers.create_user(
                username='another_user',
                email='b@c.com')

        self.path = Path.new('local_path',
                             'remote_path',
                             False)

        self.filename = 'test_filename'

        self.file = File.new(self.filename,
                             self.path)
        self.file2 = File.new('test_another_filename',
                              self.path)

        self.old_vp = VideoProgress.new(
                self.user,
                'test_filename',
                'test_hashed_filename',
                100,
                self.file)

    def test_new_file_vp(self):
        vp = VideoProgress.createOrUpdate(
                self.user,
                'test_another_filename',
                'test_another_hashed_filename',
                100,
                self.file2)
        self.assertNotEqual(self.old_vp, vp)

    def test_new_user_vp(self):
        vp = VideoProgress.createOrUpdate(
                self.user2,
                'test_another_filename',
                'test_another_hashed_filename',
                100,
                self.file)
        self.assertNotEqual(self.old_vp, vp)

    def test_return_existing(self):
        vp = VideoProgress.createOrUpdate(
                self.user,
                'test_filename',
                'test_hashed_filename',
                100,
                self.file)
        self.assertEqual(self.old_vp, vp)
