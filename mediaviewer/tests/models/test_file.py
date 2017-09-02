import mock

from django.test import TestCase
from mediaviewer.models.file import File
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.path import Path
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.posterfile import PosterFile

class TestGetScrapedNameReplacements(TestCase):
    ''' The purpose of this test is to test the period and hyphen substitutions '''
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
        self.assertEqual(expected, actual)

    def test_filename_contains_hyphen_with_subPeriod_scraper(self):
        self.file.filename = 'This-is-a-sample-file'
        self.scraper.subPeriods = True
        expected = 'This Is A Sample File'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)

    def test_filename_contains_period_without_subPeriod_scraper(self):
        self.scraper.subPeriods = False
        expected = 'This.is.a.sample.file'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)

    def test_filename_contains_hyphen_without_subPeriod_scraper(self):
        self.file.filename = 'This-is-a-sample-file'
        self.scraper.subPeriods = False
        expected = 'This-is-a-sample-file'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)

class TestGetScrapedNameOverrideFileName(TestCase):
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
        self.assertEqual(expected, actual)

    def test_override_filename(self):
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = 'overrided file name'

        expected = 'overrided file name'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)

    def test_scrapedName_uses_path_override(self):
        self.path.override_display_name = 'overrided path name'
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = None

        expected = 'overrided path name'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)

    def test_scrapedName_uses_overrided_file_name(self):
        self.path.override_display_name = 'overrided path name'
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = 'overrided file name'

        expected = 'overrided file name'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)

class TestNew(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch('mediaviewer.models.file.UserSettings.objects.filter')
        self.mock_filter = self.filter_patcher.start()

        self.createLastWatchedMessage_patcher = mock.patch('mediaviewer.models.file.Message.createLastWatchedMessage')
        self.mock_createLastWatchedMessage = self.createLastWatchedMessage_patcher.start()

        self.mock_setting = mock.MagicMock(UserSettings)
        self.mock_settings_queryset = [self.mock_setting]
        self.mock_filter.return_value.all.return_value = self.mock_settings_queryset

        self.path = Path.new('local_path', 'remote_path', False)
        self.path.save()

    def tearDown(self):
        self.filter_patcher.stop()
        self.createLastWatchedMessage_patcher.stop()

    def test_(self):
        new_file = File.new('test_filename',
                            self.path)

        self.mock_filter.assert_called_once_with(last_watched=self.path)
        self.mock_createLastWatchedMessage.assert_called_once_with(self.mock_setting.user, new_file)

class TestDestroyPosterFile(TestCase):
    def setUp(self):
        self.get_patcher = mock.patch('mediaviewer.models.file.PosterFile.objects.get')
        self.mock_get = self.get_patcher.start()

        self.log_patcher = mock.patch('mediaviewer.models.file.log')
        self.mock_log = self.log_patcher.start()

        self.path = Path.new('local_path', 'remote_path', False)
        self.path.save()

        self.file = File.new('test_filename',
                                 self.path)

        self.posterfile = mock.MagicMock(PosterFile)
        self.mock_get.return_value = self.posterfile

    def tearDown(self):
        self.get_patcher.stop()
        self.log_patcher.stop()

    def test_valid(self):
        self.file.destroyPosterFile()
        self.mock_get.assert_called_once_with(file=self.file)
        self.posterfile.delete.assert_called_once_with()

    def test_no_posterfile(self):
        self.mock_get.side_effect = PosterFile.DoesNotExist

        self.file.destroyPosterFile()
        self.mock_get.assert_called_once_with(file=self.file)
        self.assertFalse(self.posterfile.delete.called)
        self.mock_log.debug.assert_any_call('Posterfile does not exist. Continuing.')

    def test_other_exception(self):
        self.mock_get.side_effect = Exception

        self.file.destroyPosterFile()
        self.mock_get.assert_called_once_with(file=self.file)
        self.assertFalse(self.posterfile.delete.called)
        self.mock_log.error.assert_any_call('Got an error destroying posterfile')
