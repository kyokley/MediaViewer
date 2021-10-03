import mock
import pytest

from datetime import datetime

from django.contrib.auth.models import User

from mediaviewer.models.file import File
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.path import Path
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.datatransmission import DataTransmission


class TestGetScrapedNameReplacements:
    """ Test period and hyphen substitutions """
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.path = Path()
        self.path.override_display_name = None

        self.scraper = FilenameScrapeFormat()
        self.scraper.useSearchTerm = True
        self.file = File()
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = None
        self.file.rawSearchString = lambda: self.file.filename
        self.file.filenamescrapeformat = self.scraper
        self.file.path = self.path

    def test_filename_contains_period_with_subPeriod_scraper(self):
        self.scraper.subPeriods = True
        expected = 'This Is A Sample File'
        actual = self.file.getScrapedName()
        assert expected == actual

    def test_filename_contains_hyphen_with_subPeriod_scraper(self):
        self.file.filename = 'This-is-a-sample-file'
        self.scraper.subPeriods = True
        expected = 'This Is A Sample File'
        actual = self.file.getScrapedName()
        assert expected == actual

    def test_filename_contains_period_without_subPeriod_scraper(self):
        self.scraper.subPeriods = False
        expected = 'This.is.a.sample.file'
        actual = self.file.getScrapedName()
        assert expected == actual

    def test_filename_contains_hyphen_without_subPeriod_scraper(self):
        self.file.filename = 'This-is-a-sample-file'
        self.scraper.subPeriods = False
        expected = 'This-is-a-sample-file'
        actual = self.file.getScrapedName()
        assert expected == actual


class TestGetScrapedNameOverrideFileName:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.path = Path()
        self.path.override_display_name = None
        self.file = File()
        self.file.path = self.path

    def test_no_override_filename(self):
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = None

        expected = 'This.is.a.sample.file'
        actual = self.file.getScrapedName()
        assert expected == actual

    def test_override_filename(self):
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = 'overrided file name'

        expected = 'overrided file name'
        actual = self.file.getScrapedName()
        assert expected == actual

    def test_scrapedName_uses_path_override(self):
        self.path.override_display_name = 'overrided path name'
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = None

        expected = 'overrided path name'
        actual = self.file.getScrapedName()
        assert expected == actual

    def test_scrapedName_uses_overrided_file_name(self):
        self.path.override_display_name = 'overrided path name'
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = 'overrided file name'

        expected = 'overrided file name'
        actual = self.file.getScrapedName()
        assert expected == actual


@pytest.mark.django_db
class TestNew:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            'mediaviewer.models.file.UserSettings.objects.filter')

        self.mock_createLastWatchedMessage = mocker.patch(
            'mediaviewer.models.file.Message.createLastWatchedMessage')

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = (
            self.mock_settings_queryset)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)
        self.path.save()

    def test_(self):
        new_file = File.new('test_filename',
                            self.path)

        self.mock_filter.assert_called_once_with(last_watched=self.path)
        self.mock_createLastWatchedMessage.assert_called_once_with(
            self.mock_setting.user, new_file)


@pytest.mark.django_db
class TestDestroyPosterFile:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get = mocker.patch(
            'mediaviewer.models.file.PosterFile.objects.get')

        self.mock_log = mocker.patch(
            'mediaviewer.models.file.log')

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)
        self.path.save()

        self.file = File.new('test_filename',
                             self.path)

        self.posterfile = mock.MagicMock(PosterFile)
        self.mock_get.return_value = self.posterfile

    def test_valid(self):
        self.file.destroyPosterFile()
        self.mock_get.assert_called_once_with(file=self.file)
        self.posterfile.delete.assert_called_once_with()

    def test_no_posterfile(self):
        self.mock_get.side_effect = PosterFile.DoesNotExist

        self.file.destroyPosterFile()
        self.mock_get.assert_called_once_with(file=self.file)
        assert not self.posterfile.delete.called
        self.mock_log.debug.assert_any_call(
            'Posterfile does not exist. Continuing.')

    def test_other_exception(self):
        self.mock_get.side_effect = Exception

        self.file.destroyPosterFile()
        self.mock_get.assert_called_once_with(file=self.file)
        assert not self.posterfile.delete.called
        self.mock_log.error.assert_any_call(
            'Got an error destroying posterfile')


@pytest.mark.django_db
class TestIsFileNotPath:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            'mediaviewer.models.file.UserSettings.objects.filter')

        self.mock_createLastWatchedMessage = mocker.patch(
            'mediaviewer.models.file.Message.createLastWatchedMessage')

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = (
            self.mock_settings_queryset)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)
        self.path.save()

        self.new_file = File.new('test_filename',
                                 self.path)

    def test_isFile(self):
        assert self.new_file.isFile

    def test_not_isPath(self):
        assert not self.new_file.isPath


@pytest.mark.django_db
class TestProperty:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            'mediaviewer.models.file.UserSettings.objects.filter')

        self.mock_createLastWatchedMessage = mocker.patch(
            'mediaviewer.models.file.Message.createLastWatchedMessage')

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = (
            self.mock_settings_queryset)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)
        self.path.save()

        self.another_path = Path.objects.create(localpathstr='local_another_path',
                                                remotepathstr='remote_another_path',
                                                is_movie=False)
        self.another_path.save()

        self.new_file = File.new('test_filename',
                                 self.path)

        self.new_posterfile = PosterFile.new(file=self.new_file)

    def tearDown(self):
        self.filter_patcher.stop()
        self.createLastWatchedMessage_patcher.stop()

    def test_get_pathid(self):
        assert self.new_file.pathid == self.path.id

    def test_set_pathid(self):
        self.new_file.pathid = self.another_path.id
        assert self.new_file.path == self.another_path

    def test_get_posterfile(self):
        assert self.new_file.posterfile == self.new_posterfile


@pytest.mark.django_db
class TestDateCreatedForSpan:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            'mediaviewer.models.file.UserSettings.objects.filter')

        self.mock_createLastWatchedMessage = mocker.patch(
            'mediaviewer.models.file.Message.createLastWatchedMessage')

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = (
            self.mock_settings_queryset)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)

        self.another_path = Path.objects.create(localpathstr='local_another_path',
                                                remotepathstr='remote_another_path',
                                                is_movie=False)

        self.new_file = File.new('test_filename',
                                 self.path)
        self.new_file.datecreated = datetime(2018, 5, 12)

    def test_valid(self):
        assert self.new_file.dateCreatedForSpan() == '2018-05-12T00:00:00'


@pytest.mark.django_db
class TestCamelCasedProperties:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            'mediaviewer.models.file.UserSettings.objects.filter')

        self.mock_createLastWatchedMessage = mocker.patch(
            'mediaviewer.models.file.Message.createLastWatchedMessage')

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = (
            self.mock_settings_queryset)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)

        self.another_path = Path.objects.create(localpathstr='local_another_path',
                                                remotepathstr='remote_another_path',
                                                is_movie=False)

        self.datatransmission = DataTransmission()

        self.new_file = File.new('test_filename',
                                 self.path)
        self.new_file.datatransmission = self.datatransmission

    def test_fileName(self):
        assert self.new_file.fileName == self.new_file.filename

    def test_dataTransmission(self):
        assert self.new_file.dataTransmission == self.new_file.datatransmission


@pytest.mark.django_db
class TestDownloadLink:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_filter = mocker.patch(
            'mediaviewer.models.file.UserSettings.objects.filter')

        self.mock_createLastWatchedMessage = mocker.patch(
            'mediaviewer.models.file.Message.createLastWatchedMessage')

        mocker.patch(
            'mediaviewer.models.file.LOCAL_IP', 'test_local_ip')

        mocker.patch(
            'mediaviewer.models.file.BANGUP_IP', 'test_bangup_ip')

        self.mock_conf_settings = mocker.patch(
            'mediaviewer.models.file.conf_settings')

        self.mock_conf_settings.WAITER_HEAD = 'test_local_ip'

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = (
            self.mock_settings_queryset)

        self.path = Path.objects.create(localpathstr='local_path',
                                        remotepathstr='remote_path',
                                        is_movie=False)

        self.another_path = Path.objects.create(localpathstr='local_another_path',
                                                remotepathstr='remote_another_path',
                                                is_movie=False)

        self.datatransmission = DataTransmission()

        self.new_file = File.new('test_filename',
                                 self.path)
        self.new_file.datatransmission = self.datatransmission

        self.user = mock.MagicMock(User)
        self.user_settings = mock.MagicMock(UserSettings)
        self.user.settings.return_value = self.user_settings

    def test_local_ip(self):
        self.user_settings.ip_format = 'test_local_ip'


@pytest.mark.django_db
class TestMoviesOrderedByID:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file2 = File.new('tv.file2', self.tv_path)

        self.hidden_tv_file = File.new(
            'hidden.tv.file',
            self.tv_path,
            hide=True)

        self.movie_file = File.new('movie.file', self.movie_path)
        self.movie_file2 = File.new('movie.file2', self.movie_path)
        self.hidden_movie_file = File.new(
            'hidden.movie.file',
            self.movie_path,
            hide=True)

    def test_movie_files(self):
        expected = [self.movie_file2,
                    self.movie_file]
        actual = list(File.movies_ordered_by_id())

        assert expected == actual
