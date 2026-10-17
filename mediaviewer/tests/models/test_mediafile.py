import pytest
from django.db import DatabaseError

from mediaviewer.models import FilenameScrapeFormat, MediaFile, Poster


@pytest.mark.django_db
@pytest.mark.parametrize("use_tv", (True, False))
def test_delete(create_movie_media_file, create_tv_media_file, use_tv):
    if use_tv:
        mf = create_tv_media_file()
    else:
        mf = create_movie_media_file()

    Poster.objects.from_ref_obj(mf)

    MediaFile.objects.all().delete()
    assert not MediaFile.objects.filter(pk=mf.id).exists()


@pytest.mark.django_db
def test_ensure_episode_fields_parses_standard_filename_without_scraper(
    create_tv, mocker
):
    tv = create_tv(name="Standard Show")
    media_file = MediaFile.objects.create(
        media_path=tv.media_path,
        filename="Standard.Show.S01E02.mkv",
        display_name="Original display name",
    )
    configured_parse = mocker.patch.object(
        FilenameScrapeFormat, "_parse_configured_filename"
    )
    resolve_name = mocker.patch("mediaviewer.thetvdb.resolve_series_name")

    media_file.ensure_episode_fields()
    media_file.refresh_from_db()

    assert (media_file.season, media_file.episode) == (1, 2)
    assert media_file.filename == "Standard.Show.S01E02.mkv"
    assert media_file.display_name == "S01 E02"
    assert media_file.poster.episodename == ""
    configured_parse.assert_not_called()
    resolve_name.assert_not_called()


@pytest.mark.django_db
def test_ensure_episode_fields_uses_configured_parser_fallback(create_tv, mocker):
    tv = create_tv(name="Configured Show")
    FilenameScrapeFormat.new(
        nameRegex=r"^(.*?)(?= S\d+E\d+)",
        seasonRegex=r"S(\d+)E\d+",
        episodeRegex=r"S\d+E(\d+)",
    )
    media_file = MediaFile.objects.create(
        media_path=tv.media_path, filename="Configured Show S03E04.mkv"
    )
    mocker.patch("mediaviewer.thetvdb.parse_tv_filename", return_value=None)

    media_file.ensure_episode_fields()

    media_file.refresh_from_db()
    assert (media_file.season, media_file.episode) == (3, 4)
    assert media_file._poster_id


@pytest.mark.django_db
def test_ensure_episode_fields_ignores_malformed_configured_regex(create_tv):
    tv = create_tv()
    FilenameScrapeFormat.new(
        nameRegex="[",
        seasonRegex="[",
        episodeRegex="[",
    )
    media_file = MediaFile.objects.create(
        media_path=tv.media_path, filename="Unparseable filename.mkv"
    )

    media_file.ensure_episode_fields()

    media_file.refresh_from_db()
    assert media_file.season is None
    assert media_file.episode is None
    assert media_file._poster_id is None


@pytest.mark.django_db
def test_ensure_episode_fields_does_not_swallow_database_errors(create_tv, mocker):
    tv = create_tv()
    media_file = MediaFile.objects.create(
        media_path=tv.media_path, filename="Unparseable filename.mkv"
    )
    mocker.patch("mediaviewer.thetvdb.parse_tv_filename", return_value=None)
    mocker.patch.object(
        FilenameScrapeFormat,
        "_parse_configured_filename",
        side_effect=DatabaseError("database unavailable"),
    )

    with pytest.raises(DatabaseError, match="database unavailable"):
        media_file.ensure_episode_fields()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "parsed",
    (
        ("Bad Show", 1, 0),
        ("Bad Show", 32768, 1),
        ("Bad Show", 1, 32768),
        ("Bad Show", "not-a-number", 1),
    ),
)
def test_ensure_episode_fields_fails_closed_on_invalid_parse(create_tv, mocker, parsed):
    tv = create_tv()
    media_file = MediaFile.objects.create(
        media_path=tv.media_path, filename="invalid.mp4"
    )
    mocker.patch("mediaviewer.thetvdb.parse_tv_filename", return_value=parsed)
    mocker.patch.object(
        FilenameScrapeFormat, "_parse_configured_filename", return_value=None
    )

    media_file.ensure_episode_fields()

    media_file.refresh_from_db()
    assert media_file.season is None
    assert media_file.episode is None
    assert media_file._poster_id is None


@pytest.mark.django_db
def test_ensure_episode_fields_accepts_season_zero_and_preserves_poster(
    create_tv, mocker
):
    tv = create_tv()
    poster = Poster.objects.create(episodename="Pilot", tmdb="existing")
    media_file = MediaFile.objects.create(
        media_path=tv.media_path,
        filename="zero-season.mkv",
        season=0,
        _poster=poster,
    )
    mocker.patch(
        "mediaviewer.thetvdb.parse_tv_filename",
        return_value=("Show", 0, 1),
    )

    media_file.ensure_episode_fields()

    media_file.refresh_from_db()
    poster.refresh_from_db()
    assert media_file.season == 0
    assert media_file.episode == 1
    assert media_file._poster_id == poster.pk
    assert poster.episodename == "Pilot"
    assert poster.tmdb == "existing"
    assert media_file.display_name == "S00 E01: Pilot"


@pytest.mark.django_db
@pytest.mark.parametrize("parsed", (("Show", 3, 4), ("Show", 2, 4)))
def test_ensure_episode_fields_preserves_partial_coordinate_conflicts(
    create_tv, mocker, parsed
):
    tv = create_tv()
    media_file = MediaFile.objects.create(
        media_path=tv.media_path, filename="partial.mp4", season=2
    )
    mocker.patch("mediaviewer.thetvdb.parse_tv_filename", return_value=parsed)

    media_file.ensure_episode_fields()

    media_file.refresh_from_db()
    if parsed[1] == 3:
        assert media_file.episode is None
        assert media_file._poster_id is None
    else:
        assert media_file.season == 2
        assert media_file.episode == 4
        assert media_file._poster_id


@pytest.mark.django_db
def test_populate_display_name_adds_title_only_when_present(
    create_tv, create_movie_media_file
):
    tv = create_tv()
    media_file = MediaFile.objects.create(
        media_path=tv.media_path,
        filename="episode.mkv",
        season=1,
        episode=2,
    )
    media_file.populate_display_name()
    assert media_file.display_name == "S01 E02"

    poster = Poster.objects.create(episodename="The Beginning")
    media_file._poster = poster
    media_file.populate_display_name()
    assert media_file.display_name == "S01 E02: The Beginning"

    movie_file = create_movie_media_file(filename="Movie.mkv")
    movie_file.populate_display_name()
    assert movie_file.display_name == movie_file.movie.name
