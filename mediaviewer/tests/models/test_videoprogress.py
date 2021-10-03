import pytest

from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

from mediaviewer.tests import helpers
from mediaviewer.utils import getSomewhatUniqueID


class BaseVPTest:
    def setUp(self):
        self.user = helpers.create_user(random=True)
        self.user2 = helpers.create_user(random=True)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)

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


@pytest.mark.django_db
class TestDestroy(BaseVPTest):
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_clearLastWatchedMessage = mocker.patch('mediaviewer.models.videoprogress.Message.clearLastWatchedMessage')

        super().setUp()

    def test_no_videoprogress(self):
        expected = None
        actual = VideoProgress.destroy(self.user,
                                       'non-existent_filename_hash')

        assert expected == actual
        assert not self.mock_clearLastWatchedMessage.called
        assert [self.vp] == list(VideoProgress.objects.all())

    def test_no_next(self):
        expected = None
        actual = VideoProgress.destroy(
            self.user,
            self.hashed_filename)

        assert expected == actual
        self.mock_clearLastWatchedMessage.assert_called_once_with(self.user)
        assert not VideoProgress.objects.exists()

    def test_with_next_file(self):
        File.new('test_filename2',
                 self.path)

        expected = None
        actual = VideoProgress.destroy(
            self.user,
            self.hashed_filename)

        assert expected == actual
        assert not self.mock_clearLastWatchedMessage.called
        assert not VideoProgress.objects.exists()


@pytest.mark.django_db
class TestCreateOrUpdate(BaseVPTest):
    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()

    def test_new_file_vp(self):
        vp = VideoProgress.createOrUpdate(
            self.user,
            self.filename2,
            self.hashed_filename2,
            100,
            self.file2)
        assert self.vp != vp

    def test_new_user_vp(self):
        vp = VideoProgress.createOrUpdate(
            self.user2,
            self.filename2,
            self.hashed_filename2,
            100,
            self.file)
        assert self.vp != vp

    def test_return_existing(self):
        vp = VideoProgress.createOrUpdate(
            self.user,
            self.filename,
            self.hashed_filename,
            100,
            self.file)
        assert self.vp == vp


@pytest.mark.django_db
class TestGet(BaseVPTest):
    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()

    def test_no_matching_vp(self):
        vp = VideoProgress.get(
            self.user,
            self.hashed_filename2)
        assert vp is None

    def test_nomatching_for_user(self):
        vp = VideoProgress.get(
            self.user2,
            self.hashed_filename)
        assert vp is None

    def test_found(self):
        vp = VideoProgress.get(
            self.user,
            self.hashed_filename)
        assert self.vp == vp


@pytest.mark.django_db
class TestNew(BaseVPTest):
    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()

    def test_new(self):
        test_filename = getSomewhatUniqueID()
        hashed_filename = getSomewhatUniqueID()

        vp = VideoProgress.new(
            self.user,
            test_filename,
            hashed_filename,
            100,
            self.file2)

        assert vp.user == self.user
        assert vp.filename == test_filename
        assert vp.hashed_filename == hashed_filename
        assert vp.offset == 100
        assert vp.file == self.file2
