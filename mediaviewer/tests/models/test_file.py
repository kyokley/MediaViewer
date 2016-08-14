from django.test import TestCase
from mediaviewer.models.file import File
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat

class TestGetScrapedNameReplacements(TestCase):
    ''' The purpose of this test is to test the period and hyphen substitutions '''
    def setUp(self):
        self.scraper = FilenameScrapeFormat()
        self.scraper.useSearchTerm = True
        self.file = File()
        self.file.filename = 'This.is.a.sample.file'
        self.file.override_filename = None
        self.file.rawSearchString = lambda: self.file.filename
        self.file.filenamescrapeformat = self.scraper

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
        self.file = File()

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
