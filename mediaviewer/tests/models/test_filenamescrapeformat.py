import pytest

from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat


@pytest.mark.django_db
class TestValidForFilename:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv, create_tv_media_file):
        self.tv = create_tv(name="Foo Is Bar")
        self.tv_mf = create_tv_media_file(tv=self.tv)

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

        expected = (self.tv, "Foo is bar", "02", "01")
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


@pytest.mark.django_db
class TestTvForFilename:
    def _mock_tvdb(self, mocker, title="Example Show", season=1, episode=2):
        parse = mocker.patch(
            "mediaviewer.thetvdb.parse_tv_filename",
            return_value=(title, season, episode),
        )
        resolve = mocker.patch(
            "mediaviewer.thetvdb.resolve_series_name",
            return_value="Example Show",
        )
        return parse, resolve

    def test_standard_parse_resolves_show_and_creates_configured_b2_path(
        self, mocker, create_tv
    ):
        tv = create_tv(name="Example Show")
        local_path = tv.media_path
        local_path._path = "/library/Example Show"
        local_path.save()
        parse, resolve = self._mock_tvdb(mocker)
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_BUCKET_NAME",
            "configured-bucket",
        )
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_NAME_PREFIX",
            "tv/",
        )

        result = FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv")

        parse.assert_called_once_with("Example.Show.S01E02.mkv")
        resolve.assert_called_once_with("Example Show")
        assert result._path == "b2://configured-bucket/tv/Example Show/"
        assert result.tv_id == tv.pk
        assert local_path.refresh_from_db() is None
        assert local_path._path == "/library/Example Show"
        assert tv.mediapath_set.count() == 2

    def test_repeated_inference_reuses_created_b2_path(self, mocker, create_tv):
        tv = create_tv(name="Example Show")
        self._mock_tvdb(mocker)
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_BUCKET_NAME",
            "bucket",
        )
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_NAME_PREFIX", "tv/"
        )

        first = FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv")
        second = FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv")

        assert second.pk == first.pk
        assert tv.mediapath_set.count() == 2

    def test_existing_current_b2_path_is_returned_unchanged(self, mocker, create_tv):
        tv = create_tv(name="Example Show")
        current = tv.media_path
        current._path = "b2://existing-bucket/existing/Show/"
        current.skip = True
        current.save()
        self._mock_tvdb(mocker)
        create = mocker.patch(
            "mediaviewer.models.mediapath.MediaPath.objects.get_or_create"
        )

        result = FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv")

        assert result.pk == current.pk
        assert result._path == "b2://existing-bucket/existing/Show/"
        assert result.skip
        create.assert_not_called()

    def test_older_b2_path_is_reused_when_newest_path_is_local(
        self, mocker, create_tv, create_media_path
    ):
        tv = create_tv(name="Example Show")
        older_b2 = create_media_path(
            path="b2://older-bucket/tv/Example Show/", tv=tv
        )
        create_media_path(path="/newer/local/path", tv=tv)
        self._mock_tvdb(mocker)
        create = mocker.patch(
            "mediaviewer.models.mediapath.MediaPath.objects.get_or_create"
        )

        result = FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv")

        assert result.pk == older_b2.pk
        create.assert_not_called()

    def test_missing_current_path_uses_tv_name(self, mocker):
        from mediaviewer.models import TV

        tv = TV.objects.create(name="Example Show")
        self._mock_tvdb(mocker)
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_BUCKET_NAME",
            "bucket",
        )
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_NAME_PREFIX", "tv/"
        )

        result = FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv")

        assert result._path == "b2://bucket/tv/Example Show/"
        assert result.tv_id == tv.pk

    def test_empty_bucket_does_not_create_path(self, mocker, create_tv):
        tv = create_tv(name="Example Show")
        self._mock_tvdb(mocker)
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_BUCKET_NAME", ""
        )
        create = mocker.patch(
            "mediaviewer.models.mediapath.MediaPath.objects.get_or_create"
        )

        assert FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv") is None
        assert tv.mediapath_set.count() == 1
        create.assert_not_called()

    def test_custom_regex_fallback_resolves_canonical_name(
        self, mocker, create_tv
    ):
        tv = create_tv(name="Example Show")
        local_path = tv.media_path
        local_path._path = "/library/Example Show"
        local_path.save()
        FilenameScrapeFormat.new(
            nameRegex=r"([A-Za-z ]+) S",
            seasonRegex=r"(?<=S)\d+",
            episodeRegex=r"(?<=E)\d+",
        )
        parse = mocker.patch("mediaviewer.thetvdb.parse_tv_filename", return_value=None)
        resolve = mocker.patch(
            "mediaviewer.thetvdb.resolve_series_name", return_value="Example Show"
        )
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_BUCKET_NAME",
            "bucket",
        )
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_NAME_PREFIX", "tv/"
        )

        result = FilenameScrapeFormat.tv_for_filename("Example Show S02E05.mkv")

        parse.assert_called_once_with("Example Show S02E05.mkv")
        resolve.assert_called_once_with("Example Show")
        assert result.tv_id == tv.pk
        assert result._path == "b2://bucket/tv/Example Show/"

    @pytest.mark.parametrize(
        ("resolved_name", "duplicate"),
        [(None, False), ("Missing Show", False), ("Example Show", True)],
    )
    def test_unresolved_or_ambiguous_tv_does_not_create_path(
        self, mocker, create_tv, resolved_name, duplicate
    ):
        tv = create_tv(name="Example Show")
        if duplicate:
            create_tv(name="example show")
        self._mock_tvdb(mocker)
        mocker.patch(
            "mediaviewer.thetvdb.resolve_series_name", return_value=resolved_name
        )
        create = mocker.patch(
            "mediaviewer.models.mediapath.MediaPath.objects.get_or_create"
        )

        assert FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv") is None
        assert tv.mediapath_set.count() == 1
        create.assert_not_called()

    @pytest.mark.parametrize("owner_type", ["tv", "movie"])
    def test_destination_owned_by_another_media_is_not_reassigned(
        self, mocker, create_tv, create_movie, create_media_path, owner_type
    ):
        tv = create_tv(name="Example Show")
        local_path = tv.media_path
        local_path._path = "/library/Example Show"
        local_path.save()
        if owner_type == "tv":
            other_tv = create_tv(name="Other Show")
            destination = create_media_path(
                path="b2://bucket/tv/Example Show/", tv=other_tv
            )
            owner = other_tv
        else:
            movie = create_movie(name="Unrelated Movie")
            destination = create_media_path(
                path="b2://bucket/tv/Example Show/", movie=movie
            )
            owner = movie
        self._mock_tvdb(mocker)
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_BUCKET_NAME",
            "bucket",
        )
        mocker.patch(
            "mediaviewer.models.filenamescrapeformat.settings.B2_NAME_PREFIX", "tv/"
        )

        assert FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv") is None
        destination.refresh_from_db()
        assert destination.tv_id == (owner.pk if owner_type == "tv" else None)
        assert destination.movie_id == (owner.pk if owner_type == "movie" else None)
        assert tv.mediapath_set.count() == 1

    @pytest.mark.parametrize("season,episode", [(-1, 1), (0, 0), (1, -1)])
    def test_invalid_episode_numbers_fail_closed(
        self, mocker, season, episode
    ):
        self._mock_tvdb(mocker, season=season, episode=episode)
        resolve = mocker.patch("mediaviewer.thetvdb.resolve_series_name")

        assert FilenameScrapeFormat.tv_for_filename("Example.Show.S01E02.mkv") is None
        resolve.assert_not_called()
