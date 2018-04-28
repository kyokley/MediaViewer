from django.test import TestCase
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.path import Path

class TestValidForFilename(TestCase):
    def setUp(self):
        self.path = Path()
        self.path.override_display_name = 'Foo Is Bar'

        self.scraper = FilenameScrapeFormat.new(nameRegex=r'[fF]oo[\.\s\-][Ii]s[\.\s\-][Bb]ar',
                                                seasonRegex=r'(?<=[sS])\d{2}',
                                                episodeRegex=r'(?<=[eE])\d{2}')

    def test_is_valid(self):
        test_filename = 'Foo.is.bar.S02E01.mpg'

        self.assertTrue(FilenameScrapeFormat.valid_for_filename(test_filename))

    def test_is_not_valid(self):
        test_filename = 'Foo.is.not.bar.S02E01.mpg'

        self.assertFalse(FilenameScrapeFormat.valid_for_filename(test_filename))
