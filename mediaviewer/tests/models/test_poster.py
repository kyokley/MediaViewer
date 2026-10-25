from typing import cast

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import DatabaseError
from django.db.models.fields.files import FieldFile
from django.test import override_settings

from mediaviewer.models import Poster
from mediaviewer.models.poster import _get_cast_data

sample_good_result = {
    "backdrop_path": "/asdfasdf.jpg",
    "first_air_date": "2016-09-30",
    "genre_ids": [18, 10765],
    "id": 12345,
    "name": "show name",
    "origin_country": ["US"],
    "original_language": "en",
    "original_name": "show name",
    "overview": "show description",
    "popularity": 4.278642,
    "poster_path": "/zxcvzxcv.jpg",
    "vote_average": 6.81,
    "vote_count": 41,
}

sample_good_crew = {
    "id": 12345,
    "cast": [
        {
            "cast_id": 2345,
            "character": "John Doe",
            "credit_id": "3456",
            "id": 4567,
            "name": "Alex Reporter",
            "order": 0,
        }
    ],
    "crew": [
        {
            "credit_id": 18365,
            "department": "Directing",
            "id": 582,
            "job": "Director",
            "name": "Jim Pope",
            "order": 0,
        },
        {
            "credit_id": 18365,
            "department": "Directing",
            "id": 582,
            "job": "Director",
            "name": "Jim Pope",
            "order": 0,
        },
    ],
}

sample_bad_result = {"page": 1, "results": [], "total_pages": 1, "total_results": 0}


@pytest.mark.django_db
def test_episode_metadata_enrichment_uses_integer_coordinates(
    create_tv_media_file, mocker
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 0
    media_file.episode = 1
    media_file.save()
    poster = Poster.objects.get(pk=media_file.poster.pk)
    poster.tmdb = "123"
    get_episode_info = mocker.patch(
        "mediaviewer.models.poster.getTVDBEpisodeInfo",
        return_value={"name": "Episode title", "id": 456},
    )

    poster._tmdb_episode_info()

    media_file.refresh_from_db()
    get_episode_info.assert_called_once_with("123", 0, 1)
    assert poster.episodename == "Episode title"
    assert media_file.display_name.endswith("Episode title")


def test_cast_data_uses_season_zero_episode_url(mocker):
    get_json = mocker.patch("mediaviewer.models.poster.getJSONData", return_value={})

    _get_cast_data("123", season=0, episode=1, is_movie=False)

    assert "/season/0/episode/1/credits" in get_json.call_args_list[0].args[0]


@pytest.mark.django_db
def test_tv_media_file_population_uses_parent_id_and_keeps_core_data_on_optional_failures(
    create_tv_media_file, mocker
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 0
    media_file.episode = 1
    media_file.save()
    parent_poster = Poster.objects.from_ref_obj(media_file.tv)
    parent_poster.tmdb = "series-123"
    parent_poster.save()
    poster = Poster.objects.get(pk=media_file.poster.pk)
    poster.image = "uploads/existing.jpg"
    poster.save()

    episode_info = mocker.patch(
        "mediaviewer.models.poster.getTVDBEpisodeInfo",
        return_value={
            "name": "Episode title",
            "overview": "Episode overview",
            "air_date": "2024-01-02",
            "id": 789,
            "still_path": "/still.jpg",
        },
    )
    mocker.patch("mediaviewer.models.poster.requests.get", side_effect=RuntimeError)
    mocker.patch(
        "mediaviewer.models.poster._get_extended_info", side_effect=RuntimeError
    )
    mocker.patch("mediaviewer.models.poster._get_cast_data", return_value=["malformed"])

    poster.populate_data()

    episode_info.assert_called_once_with("series-123", 0, 1)
    poster.refresh_from_db()
    parent_poster.refresh_from_db()
    assert poster.episodename == "Episode title"
    assert poster.extendedplot == "Episode overview"
    assert poster.release_date.isoformat() == "2024-01-02"
    assert poster.tmdb == "789"
    assert poster.image.name == "uploads/existing.jpg"
    assert parent_poster.tmdb == "series-123"
    media_file.refresh_from_db()
    assert media_file.display_name.endswith("Episode title")


@pytest.mark.django_db
def test_tv_media_file_retry_never_uses_episode_id_as_series_id(
    create_tv_media_file, mocker
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 1
    media_file.episode = 2
    media_file.save()
    parent_poster = Poster.objects.from_ref_obj(media_file.tv)
    parent_poster.tmdb = "series-123"
    parent_poster.save()
    poster = media_file.poster
    poster.tmdb = "episode-789"
    poster.save()
    episode_info = mocker.patch(
        "mediaviewer.models.poster.getTVDBEpisodeInfo",
        side_effect=[
            {"name": "Episode title", "id": "episode-789"},
            {"name": "Episode title", "id": "episode-789"},
        ],
    )
    mocker.patch("mediaviewer.models.poster._get_extended_info", return_value={})
    mocker.patch("mediaviewer.models.poster._get_cast_data", return_value={})
    series_detail = mocker.patch(
        "mediaviewer.models.poster.getJSONData", side_effect=RuntimeError
    )

    poster.populate_data()
    poster.populate_data()

    assert [call.args[0] for call in episode_info.call_args_list] == [
        "series-123",
        "series-123",
    ]
    assert all(
        "/tv/episode-789?" not in call.args[0] for call in series_detail.call_args_list
    )


@pytest.mark.django_db
def test_tv_media_file_resolves_missing_parent_id_without_parent_population(
    create_tv_media_file, mocker
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 1
    media_file.episode = 2
    media_file.save()
    tv = media_file.tv
    assert tv._poster_id is None
    search = mocker.patch(
        "mediaviewer.models.poster.getJSONData",
        return_value={"results": [{"id": 456, "name": tv.name}]},
    )
    parent_populate = mocker.patch("mediaviewer.models.media.Media._populate_poster")
    episode_info = mocker.patch(
        "mediaviewer.models.poster.getTVDBEpisodeInfo", return_value={}
    )
    mocker.patch("mediaviewer.models.poster._get_extended_info", return_value={})
    mocker.patch("mediaviewer.models.poster._get_cast_data", return_value={})
    mocker.patch.object(Poster, "_populate_tv_series_details")

    media_file.poster.populate_data()

    assert "search/tv" in search.call_args.args[0]
    tv.refresh_from_db()
    parent_poster = Poster.objects.get(pk=tv._poster_id)
    assert parent_poster.tmdb == "456"
    parent_populate.assert_not_called()
    episode_info.assert_called_once_with("456", 1, 2)


@pytest.mark.django_db
def test_tv_name_search_uses_unique_exact_match_not_first_result(
    create_tv_media_file, mocker
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 1
    media_file.episode = 2
    media_file.save()
    tv = media_file.tv
    mocker.patch(
        "mediaviewer.models.poster.getJSONData",
        return_value={
            "results": [
                {"id": 111, "name": "Unrelated Show"},
                {"id": 456, "original_name": tv.name.lower()},
            ]
        },
    )
    episode_info = mocker.patch(
        "mediaviewer.models.poster.getTVDBEpisodeInfo", return_value={}
    )
    mocker.patch("mediaviewer.models.poster._get_extended_info", return_value={})
    mocker.patch("mediaviewer.models.poster._get_cast_data", return_value={})
    mocker.patch.object(Poster, "_populate_tv_series_details")

    media_file.poster.populate_data()

    tv.refresh_from_db()
    assert Poster.objects.get(pk=tv._poster_id).tmdb == "456"
    episode_info.assert_called_once_with("456", 1, 2)


@pytest.mark.django_db
def test_tv_name_search_rejects_duplicate_exact_matches(create_tv_media_file, mocker):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 1
    media_file.episode = 2
    media_file.save()
    tv = media_file.tv
    mocker.patch(
        "mediaviewer.models.poster.getJSONData",
        return_value={
            "results": [
                {"id": 111, "name": tv.name},
                {"id": 456, "original_name": tv.name},
            ]
        },
    )
    episode_info = mocker.patch("mediaviewer.models.poster.getTVDBEpisodeInfo")

    media_file.poster.populate_data()

    tv.refresh_from_db()
    assert Poster.objects.get(pk=tv._poster_id).tmdb == ""
    episode_info.assert_not_called()


@pytest.mark.django_db
def test_parent_identity_database_error_propagates_without_name_search(
    create_tv_media_file, mocker
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 1
    media_file.episode = 2
    media_file.save()
    Poster.objects.from_ref_obj(media_file.tv)
    search = mocker.patch(
        "mediaviewer.models.poster.getJSONData",
        return_value={"results": [{"id": 456, "name": media_file.tv.name}]},
    )
    mocker.patch.object(Poster, "_populate_tv_series_details")
    original_save = Poster.save

    def fail_identity_save(poster, *args, **kwargs):
        if kwargs.get("update_fields") == ["tmdb"]:
            raise DatabaseError("db failure")
        return original_save(poster, *args, **kwargs)

    mocker.patch.object(Poster, "save", autospec=True, side_effect=fail_identity_save)

    with pytest.raises(DatabaseError, match="db failure"):
        media_file.poster.populate_data()

    search.assert_called_once()


@pytest.mark.django_db
def test_tv_episode_http_population_persists_episode_and_image(
    create_tv_media_file, mocker, tmp_path
):
    media_file = create_tv_media_file(filename="show.mp4")
    media_file.season = 0
    media_file.episode = 1
    media_file.save()
    parent_poster = Poster.objects.from_ref_obj(media_file.tv)
    parent_poster.tmdb = "series-123"
    parent_poster.save()
    poster = media_file.poster
    mocker.patch(
        "mediaviewer.models.poster.getTVDBEpisodeInfo",
        return_value={
            "name": "Episode title",
            "overview": "Episode overview",
            "air_date": "2024-01-02",
            "id": 789,
            "still_path": "/still.jpg",
        },
    )
    series_request = mocker.patch(
        "mediaviewer.models.poster.getJSONData",
        return_value={"overview": "Series overview", "genres": []},
    )
    response = mocker.Mock(status_code=200)
    response.iter_content.return_value = [b"image-bytes"]
    image_request = mocker.patch(
        "mediaviewer.models.poster.requests.get", return_value=response
    )
    mocker.patch("mediaviewer.models.poster._get_extended_info", return_value={})
    mocker.patch("mediaviewer.models.poster._get_cast_data", return_value={})

    with override_settings(MEDIA_ROOT=str(tmp_path)):
        poster.populate_data()
        loaded = Poster.objects.get(pk=poster.pk)

        assert loaded.episodename == "Episode title"
        assert loaded.extendedplot == "Episode overview"
        assert loaded.plot == "Series overview"
        assert loaded.tmdb == "789"
        assert loaded.image.storage.exists(loaded.image.name)

    image_request.assert_called_once()
    assert image_request.call_args.args[0].endswith("/still.jpg")
    assert "/tv/series-123?" in series_request.call_args.args[0]


@pytest.mark.django_db
@pytest.mark.parametrize("use_tv", (True, False))
@pytest.mark.parametrize("use_mf", (True, False))
class TestFromRefObj:
    @pytest.fixture(autouse=True)
    def setUp(
        self, create_tv, create_movie, create_tv_media_file, create_movie_media_file
    ):
        self.tv = create_tv()
        self.movie = create_movie()

        self.tv_mf = create_tv_media_file(tv=self.tv)
        self.movie_mf = create_movie_media_file(movie=self.movie)

    def test_obj(self, use_tv, use_mf):
        if use_tv:
            if use_mf:
                ref_obj = self.tv_mf
            else:
                ref_obj = self.tv
        else:
            if use_mf:
                ref_obj = self.movie_mf
            else:
                ref_obj = self.movie

        new_obj = Poster.objects.from_ref_obj(ref_obj)

        assert new_obj.ref_obj == ref_obj


@pytest.mark.django_db
class TestStorePlot:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = Poster()

    def test_has_plot(self):
        test_data = {"Plot": "test_plot"}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert "test_plot" == self.test_obj.plot

    def test_has_overview(self):
        test_data = {"overview": "test_overview"}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert "test_overview" == self.test_obj.plot

    def test_has_multiple_results(self):
        test_data = {
            "results": [
                {"overview": "test_results_overview"},
            ]
        }

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert "test_results_overview" == self.test_obj.plot

    def test_plot_undefined(self):
        test_data = {"Plot": "undefined"}

        self.test_obj._store_plot(test_data)

        assert self.test_obj.plot == ""


@pytest.mark.django_db
class TestStoreGenres:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_tv):
        self.mock_tvdbConfig = mocker.patch("mediaviewer.models.poster.tvdbConfig")

        self.mock_tvdbConfig.genres = {123: "test_genre"}

        self.tv = create_tv()
        self.test_obj = Poster.objects.from_ref_obj(self.tv)

    def test_has_results(self):
        imdb_data = {
            "results": [
                {"genre_ids": [123]},
            ],
        }

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        assert expected == actual
        assert "Test_Genre" == self.test_obj.genres.all()[0].genre

    def test_has_genre_ids(self):
        imdb_data = {"genre_ids": [123]}

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        assert expected == actual
        assert "Test_Genre" == self.test_obj.genres.all()[0].genre

    def test_has_genres(self):
        imdb_data = {
            "genres": [
                {"name": "test_genre"},
            ]
        }

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        assert expected == actual
        assert "Test_Genre" == self.test_obj.genres.all()[0].genre


@pytest.mark.django_db
class TestStoreRating:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = Poster()

    def test_has_imdb_rating(self):
        test_data = {
            "imdbRating": "test_rating",
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        assert expected == actual
        assert "test_rating" == self.test_obj.rating

    def test_has_vote_average(self):
        test_data = {
            "vote_average": "test_rating",
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        assert expected == actual
        assert "test_rating" == self.test_obj.rating

    def test_undefined(self):
        test_data = {
            "vote_average": "undefined",
        }

        self.test_obj._store_rating(test_data)
        assert self.test_obj.rating == ""


@pytest.mark.django_db
class TestStoreTagline:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = Poster()

    def test_has_vote_average(self):
        test_data = {
            "tagline": "test_tagline",
        }

        expected = None
        actual = self.test_obj._store_tagline(test_data)

        assert expected == actual
        assert "test_tagline" == self.test_obj.tagline

    def test_undefined(self):
        test_data = {
            "tagline": "undefined",
        }

        self.test_obj._store_tagline(test_data)
        assert self.test_obj.tagline == ""


class TestStoreRated:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_data = {"Rated": "test_rated"}

        self.test_obj = Poster()

    def test_has_rated(self):
        self.test_obj._store_rated(self.test_data)

        assert "test_rated" == self.test_obj.rated

    def test_no_rated(self):
        self.test_data = {}

        self.test_obj._store_rated(self.test_data)
        assert self.test_obj.rated == ""

    def test_undefined(self):
        self.test_data = {"Rated": "undefined"}

        self.test_obj._store_rated(self.test_data)
        assert self.test_obj.rated == ""


@pytest.mark.django_db
class TestExternalUrl:
    IMAGE_NAME = "uploads/2026/08/13/test.png"

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = Poster()

    def test_no_image(self):
        assert self.test_obj.external_url() == ""

    @override_settings(OG_BASE_URL="https://media.example.com")
    def test_uses_og_base_url(self):
        self.test_obj.image = self.IMAGE_NAME
        image = cast(FieldFile, self.test_obj.image)

        expected = f"{settings.OG_BASE_URL}/{image.url}"

        assert self.test_obj.external_url() == expected

    @override_settings(OG_BASE_URL="")
    def test_falls_back_to_site_domain(self):
        self.test_obj.image = self.IMAGE_NAME
        image = cast(FieldFile, self.test_obj.image)
        site = Site.objects.create(domain="mytest.example.com", name="test site")

        with override_settings(SITE_ID=site.pk):
            expected = f"{settings.HTTP_PROTOCOL}://{site.domain}{image.url}"

            assert self.test_obj.external_url() == expected
