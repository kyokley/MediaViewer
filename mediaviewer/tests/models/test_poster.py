import pytest

from mediaviewer.models import Poster

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
