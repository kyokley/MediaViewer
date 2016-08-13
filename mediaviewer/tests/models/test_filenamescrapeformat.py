from django.test import TestCase
from mediaviewer.models.file import File
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat

import mock

@mock.patch('mediaviewer.models.file.File.filenamescrapeformat')
class TestGetScrapedNameReplacements(TestCase):
    ''' The purpose of this test is to test the period and hyphen substitutions '''
    def setUp(self):
        self.scraper = mock.create_autospec(FilenameScrapeFormat)
        self.scraper.useSearchTerm = True
        self.file = File()
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = None
        self.file.rawSearchString = lambda: self.file.filename
        self.file.filenamescrapeformat = self.scraper

    def test_filename_contains_period_with_subPeriod_scraper(self, mock_scraper):
        self.scraper.subPeriods = True
        expected = 'This is a sample file'
        actual = self.file.getScrapedName()
        self.assertEqual(expected, actual)
