from django.test import TestCase
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.path import Path

class TestValidForFilename(TestCase):
    def setUp(self):
        self.path = Path.new('/path/to/local',
                             '/path/to/remote',
                             is_movie=False)
        self.path.override_display_name = 'Foo Is Bar'
        self.path.save()

        self.scraper = FilenameScrapeFormat.new(nameRegex=r'[fF]oo[\.\s\-][Ii]s[\.\s\-][Bb]ar',
                                                seasonRegex=r'(?<=[sS])\d{2}',
                                                episodeRegex=r'(?<=[eE])\d{2}',
                                                subPeriods=True)

    def test_is_valid(self):
        test_filename = 'Foo.is.bar.S02E01.mpg'

        expected = self.path
        actual = self.scraper.valid_for_filename(test_filename)

        self.assertEqual(expected, actual)

    def test_name_not_valid(self):
        test_filename = 'Foo.is.not.bar.S02E01.mpg'

        expected = None
        actual = self.scraper.valid_for_filename(test_filename)

        self.assertEqual(expected, actual)

    def test_season_and_episode_not_valid(self):
        test_filename = 'Foo.is.not.bar.201.mpg'

        expected = None
        actual = self.scraper.valid_for_filename(test_filename)

        self.assertEqual(expected, actual)

    def test_no_season_not_valid(self):
        test_filename = 'Foo.is.not.bar.mpg'

        expected = None
        actual = self.scraper.valid_for_filename(test_filename)

        self.assertEqual(expected, actual)
