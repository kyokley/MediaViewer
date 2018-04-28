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

class TestPathForFilename(TestCase):
    def setUp(self):
        self.path1 = Path.new('/path/to/local',
                              '/path/to/remote',
                              is_movie=False)
        self.path1.override_display_name = 'Foo Is Bar'
        self.path1.save()

        self.path2 = Path.new('/path/to/local2',
                              '/path/to/remote2',
                              is_movie=False)
        self.path2.override_display_name = 'Foo Is Not Bar'
        self.path2.save()

        self.path3 = Path.new('/path/to/local3',
                              '/path/to/remote3',
                              is_movie=False)
        self.path3.override_display_name = 'Boo As Baz'
        self.path3.save()

        self.path4 = Path.new('/path/to/local',
                              '/path/to/remote4',
                              is_movie=False)
        self.path4.override_display_name = 'Foo Is Bar'
        self.path4.save()

        self.scraper = FilenameScrapeFormat.new(nameRegex=r'[fF]oo[\.\s\-][Ii]s[\.\s\-][Bb]ar',
                                                seasonRegex=r'(?<=[sS])\d{2}',
                                                episodeRegex=r'(?<=[eE])\d{2}',
                                                subPeriods=True)

    def test_found(self):
        test_filename = 'Foo.is.bar.S02E01.mpg'

        expected = self.path4
        actual = FilenameScrapeFormat.path_for_filename(test_filename)

        self.assertEqual(expected, actual)

    def test_not_found(self):
        test_filename = 'Foo.is.not.bar.mpg'

        expected = None
        actual = FilenameScrapeFormat.path_for_filename(test_filename)

        self.assertEqual(expected, actual)
