import mock

from django.test import TestCase
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

from mediaviewer.tests import helpers
from mediaviewer.utils import getSomewhatUniqueID


class BaseVPTest(TestCase):
    def setUp(self):
        self.user = helpers.create_user(random=True)
        self.user2 = helpers.create_user(random=True)

        self.path = Path.new('local_path',
                             'remote_path',
                             False)

        self.filename = 'test_filename'
        self.filename2 = 'test_another_filename'

        self.hashed_filename = 'test_hashed_filename'
        self.hashed_filename2 = 'test_another_hashed_filename'

        self.file = File.new(self.filename,
                             self.path)
        self.file2 = File.new(self.filename2,
                              self.path)

        self.vp = VideoProgress.new(self.user,
                                    self.filename,
                                    self.hashed_filename,
                                    100,
                                    self.file)


class TestDestroy(BaseVPTest):
    def setUp(self):
        clearLastWatchedMessage_patcher = mock.patch(
            'mediaviewer.models.videoprogress.Message.clearLastWatchedMessage')
        self.mock_clearLastWatchedMessage = (
                clearLastWatchedMessage_patcher.start())
        self.addCleanup(clearLastWatchedMessage_patcher.stop)

        super(TestDestroy, self).setUp()

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
        actual = VideoProgress.destroy(
                self.user,
                self.hashed_filename)

        self.assertEqual(expected, actual)
        self.mock_clearLastWatchedMessage.assert_called_once_with(self.user)
        self.assertFalse(VideoProgress.objects.exists())

    def test_with_next_file(self):
        File.new('test_filename2',
                 self.path)

        expected = None
        actual = VideoProgress.destroy(
                self.user,
                self.hashed_filename)

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_clearLastWatchedMessage.called)
        self.assertFalse(VideoProgress.objects.exists())


class TestCreateOrUpdate(BaseVPTest):
    def test_new_file_vp(self):
        vp = VideoProgress.createOrUpdate(
                self.user,
                self.filename2,
                self.hashed_filename2,
                100,
                self.file2)
        self.assertNotEqual(self.vp, vp)

    def test_new_user_vp(self):
        vp = VideoProgress.createOrUpdate(
                self.user2,
                self.filename2,
                self.hashed_filename2,
                100,
                self.file)
        self.assertNotEqual(self.vp, vp)

    def test_return_existing(self):
        vp = VideoProgress.createOrUpdate(
                self.user,
                self.filename,
                self.hashed_filename,
                100,
                self.file)
        self.assertEqual(self.vp, vp)


class TestGet(BaseVPTest):
    def test_no_matching_vp(self):
        vp = VideoProgress.get(
                self.user,
                self.hashed_filename2)
        self.assertIsNone(vp)

    def test_nomatching_for_user(self):
        vp = VideoProgress.get(
                self.user2,
                self.hashed_filename)
        self.assertIsNone(vp)

    def test_found(self):
        vp = VideoProgress.get(
                self.user,
                self.hashed_filename)
        self.assertEqual(self.vp, vp)


class TestNew(BaseVPTest):
    def test_new(self):
        test_filename = getSomewhatUniqueID()
        hashed_filename = getSomewhatUniqueID()

        vp = VideoProgress.new(
                self.user,
                test_filename,
                hashed_filename,
                100,
                self.file2)

        self.assertEqual(vp.user, self.user)
        self.assertEqual(vp.filename, test_filename)
        self.assertEqual(vp.hashed_filename, hashed_filename)
        self.assertEqual(vp.offset, 100)
        self.assertEqual(vp.file, self.file2)
