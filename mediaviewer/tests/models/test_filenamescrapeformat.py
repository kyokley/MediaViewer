import pytest
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat


@pytest.mark.django_db
class TestValidForFilename:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv_media_file):
        self.tv_mf = create_tv_media_file()
        self.tv_mf.display_name = "Foo Is Bar"

        self.scraper = FilenameScrapeFormat.new(
            nameRegex=r"[fF]oo[\.\s\-][Ii]s[\.\s\-][Bb]ar",
            seasonRegex=r"(?<=[sS])\d{2}",
            episodeRegex=r"(?<=[eE])\d{2}",
            subPeriods=True,
        )

        self.tv_mf.scraper = self.scraper
        self.tv_mf.save()

    def test_is_valid(self):
        test_filename = "Foo.is.bar.S02E01.mpg"

        expected = (self.tv_mf, "Foo is bar", "02", "01")
        actual = self.scraper.valid_for_filename(test_filename)

        assert expected == actual

    def test_name_not_valid(self):
        test_filename = "Foo.is.not.bar.S02E01.mpg"

        expected = None
        actual = self.scraper.valid_for_filename(test_filename)

        assert expected == actual

    def test_season_and_episode_not_valid(self):
        test_filename = "Foo.is.not.bar.201.mpg"

        expected = None
        actual = self.scraper.valid_for_filename(test_filename)

        assert expected == actual

    def test_no_season_not_valid(self):
        test_filename = "Foo.is.not.bar.mpg"

        expected = None
        actual = self.scraper.valid_for_filename(test_filename)

        assert expected == actual
