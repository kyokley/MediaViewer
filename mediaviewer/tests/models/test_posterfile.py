import mock
import pytest
from django.test import TestCase

from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

sample_good_result = {u'backdrop_path': u'/asdfasdf.jpg',
                      u'first_air_date': u'2016-09-30',
                      u'genre_ids': [18, 10765],
                      u'id': 12345,
                      u'name': u"show name",
                      u'origin_country': [u'US'],
                      u'original_language': u'en',
                      u'original_name': u"show name",
                      u'overview': u'show description',
                      u'popularity': 4.278642,
                      u'poster_path': u'/zxcvzxcv.jpg',
                      u'vote_average': 6.81,
                      u'vote_count': 41}

sample_good_crew = {'id': 12345,
                    'cast': [{'cast_id': 2345,
                              'character': 'John Doe',
                              'credit_id': '3456',
                              'id': 4567,
                              'name': 'Alex Reporter',
                              'order': 0}],
                    'crew': [{'credit_id': 18365,
                              'department': 'Directing',
                              'id': 582,
                              'job': 'Director',
                              'name': 'Jim Pope',
                              'order': 0},
                             {'credit_id': 18365,
                              'department': 'Directing',
                              'id': 582,
                              'job': 'Director',
                              'name': 'Jim Pope',
                              'order': 0}
                             ],
                    }

sample_bad_result = {u'page': 1,
                     u'results': [],
                     u'total_pages': 1,
                     u'total_results': 0}


@pytest.mark.django_db
class TestNew:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_objects = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile.objects')

        self.mock_populate_poster_data = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._populate_poster_data')

        self.path = Path.objects.create(localpathstr='local.path',
                                        remotepathstr='remote.path',
                                        is_movie=False)
        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.file = File.new('new.file.mp4',
                             self.movie_path)

        self.mock_objects.filter.return_value.first.return_value = None

    def test_no_file_no_path(self):
        with pytest.raises(ValueError):
            PosterFile.new()

    def test_path_is_movie(self):
        with pytest.raises(ValueError):
            PosterFile.new(path=self.movie_path)

    def test_file(self):
        new_obj = PosterFile.new(file=self.file)

        assert new_obj.file == self.file
        assert new_obj.path is None
        self.mock_populate_poster_data.assert_called_once_with()

    def test_path(self):
        new_obj = PosterFile.new(path=self.path)

        assert new_obj.file is None
        assert new_obj.path == self.path
        self.mock_populate_poster_data.assert_called_once_with()

    def test_existing_for_file(self):
        self.mock_objects.filter.return_value.first.return_value = (
            'existing_obj')

        existing = PosterFile.new(file=self.file)
        assert existing == 'existing_obj'
        assert not self.mock_populate_poster_data.called

    def test_existing_for_path(self):
        self.mock_objects.filter.return_value.first.return_value = (
            'existing_obj')

        existing = PosterFile.new(path=self.path)
        assert existing == 'existing_obj'
        assert not self.mock_populate_poster_data.called


@pytest.mark.django_db
class TestGetIMDBData:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getDataFromIMDB = mocker.patch(
            'mediaviewer.models.posterfile.getDataFromIMDB')

        self.mock_getDataFromIMDBByPath = mocker.patch(
            'mediaviewer.models.posterfile.getDataFromIMDBByPath')

        self.mock_cast_and_crew = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._cast_and_crew')

        self.mock_assign_tvdb_info = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._assign_tvdb_info')

        self.mock_store_extended_info = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_extended_info')

        self.mock_store_plot = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_plot')

        self.mock_store_genres = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_genres')

        self.mock_store_rated = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_rated')

        self.fake_data = {'Poster': 'test_poster',
                          'id': 123}
        self.mock_getDataFromIMDB.return_value = self.fake_data
        self.mock_getDataFromIMDBByPath.return_value = self.fake_data

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('new.file.mp4',
                                   self.movie_path)

        self.test_obj = PosterFile()

    def test_file_is_movie(self):
        self.test_obj.file = self.movie_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        assert expected == actual
        self.mock_getDataFromIMDB.assert_called_once_with(self.movie_file)
        self.mock_cast_and_crew.assert_called_once_with()
        assert 'test_poster' == self.test_obj.poster_url
        self.mock_assign_tvdb_info.assert_called_once_with()
        self.mock_store_extended_info.assert_called_once_with()
        self.mock_store_plot.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_genres.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_rated.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)

    def test_path_for_tv(self):
        self.test_obj.path = self.tv_path

        expected = self.mock_getDataFromIMDBByPath.return_value
        actual = self.test_obj._getIMDBData()

        assert expected == actual
        self.mock_getDataFromIMDBByPath.assert_called_once_with(self.tv_path)
        self.mock_cast_and_crew.assert_called_once_with()
        assert 'test_poster' == self.test_obj.poster_url
        self.mock_assign_tvdb_info.assert_called_once_with()

        self.mock_store_extended_info.assert_called_once_with()
        self.mock_store_plot.assert_called_once_with(
            self.mock_getDataFromIMDBByPath.return_value)
        self.mock_store_genres.assert_called_once_with(
            self.mock_getDataFromIMDBByPath.return_value)
        self.mock_store_rated.assert_called_once_with(
            self.mock_getDataFromIMDBByPath.return_value)

    def test_file_for_tv(self):
        self.test_obj.file = self.tv_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        assert expected == actual
        self.mock_getDataFromIMDB.assert_called_once_with(self.tv_file)
        self.mock_cast_and_crew.assert_called_once_with()
        assert 'test_poster' == self.test_obj.poster_url
        self.mock_assign_tvdb_info.assert_called_once_with()

        self.mock_store_extended_info.assert_called_once_with()
        self.mock_store_plot.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_genres.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)
        self.mock_store_rated.assert_called_once_with(
            self.mock_getDataFromIMDB.return_value)

    def test_no_data_for_movie(self):
        self.mock_getDataFromIMDB.return_value = None
        self.test_obj.file = self.movie_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        assert expected == actual
        self.mock_getDataFromIMDB.assert_called_once_with(self.movie_file)
        assert not self.mock_cast_and_crew.called
        assert self.test_obj.poster_url is None
        self.mock_assign_tvdb_info.assert_called_once_with()
        assert not self.mock_store_extended_info.called
        assert not self.mock_store_plot.called
        assert not self.mock_store_genres.called
        assert not self.mock_store_rated.called

    def test_no_data_for_path_for_tv(self):
        self.mock_getDataFromIMDBByPath.return_value = None
        self.test_obj.path = self.tv_path

        expected = self.mock_getDataFromIMDBByPath.return_value
        actual = self.test_obj._getIMDBData()

        assert expected == actual
        self.mock_getDataFromIMDBByPath.assert_called_once_with(self.tv_path)
        assert not self.mock_cast_and_crew.called
        assert self.test_obj.poster_url is None
        self.mock_assign_tvdb_info.assert_called_once_with()
        assert not self.mock_store_extended_info.called
        assert not self.mock_store_plot.called
        assert not self.mock_store_genres.called
        assert not self.mock_store_rated.called

    def test_no_data_for_file_for_tv(self):
        self.mock_getDataFromIMDB.return_value = None
        self.test_obj.file = self.tv_file

        expected = self.mock_getDataFromIMDB.return_value
        actual = self.test_obj._getIMDBData()

        assert expected == actual
        self.mock_getDataFromIMDB.assert_called_once_with(self.tv_file)
        assert not self.mock_cast_and_crew.called
        assert self.test_obj.poster_url is None
        assert not self.mock_store_extended_info.called
        assert not self.mock_store_plot.called
        assert not self.mock_store_genres.called
        assert not self.mock_store_rated.called


@pytest.mark.django_db
class TestCastAndCrew:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getCastData = mocker.patch(
            'mediaviewer.models.posterfile.getCastData')

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('new.file.mp4',
                                   self.movie_path)

        self.test_obj = PosterFile()
        self.test_obj.tmdb_id = 123
        self.test_obj.save()

        self.test_getCastData = {
            'cast': [
                {'name': 'test_actor'}],
            'crew': [
                {'job': 'Writer',
                 'name': 'test_writer'},
                {'job': 'Director',
                 'name': 'test_director'},
            ],
        }
        self.mock_getCastData.return_value = self.test_getCastData

    def test_no_cast_data(self):
        self.mock_getCastData.return_value = None
        self.test_obj.file = self.movie_file

        expected = None
        actual = self.test_obj._cast_and_crew()

        assert expected == actual
        self.mock_getCastData.assert_called_once_with(
            123,
            season=None,
            episode=None,
            isMovie=True)

        assert [] == list(self.test_obj.actors.all())
        assert [] == list(self.test_obj.writers.all())
        assert [] == list(self.test_obj.directors.all())

    def test_file_is_movie(self):
        self.test_obj.file = self.movie_file

        expected = None
        actual = self.test_obj._cast_and_crew()

        assert expected == actual
        self.mock_getCastData.assert_called_once_with(
            123,
            season=None,
            episode=None,
            isMovie=True)

        assert 'Test_Actor' == self.test_obj.actors.all()[0].name
        assert 'Test_Writer' == self.test_obj.writers.all()[0].name
        assert 'Test_Director' == self.test_obj.directors.all()[0].name

    def test_path_for_tv(self):
        self.test_obj.path = self.tv_path

        expected = None
        actual = self.test_obj._cast_and_crew()

        assert expected == actual
        self.mock_getCastData.assert_called_once_with(
            123,
            season=None,
            episode=None,
            isMovie=False)

        assert 'Test_Actor' == self.test_obj.actors.all()[0].name
        assert 'Test_Writer' == self.test_obj.writers.all()[0].name
        assert 'Test_Director' == self.test_obj.directors.all()[0].name

    def test_file_is_tv(self):
        self.test_obj.file = self.tv_file

        expected = None
        actual = self.test_obj._cast_and_crew()

        assert expected == actual
        self.mock_getCastData.assert_called_once_with(
            123,
            season=3,
            episode=5,
            isMovie=False)

        assert 'Test_Actor' == self.test_obj.actors.all()[0].name
        assert 'Test_Writer' == self.test_obj.writers.all()[0].name
        assert 'Test_Director' == self.test_obj.directors.all()[0].name


@pytest.mark.django_db
class TestTVDBEpisodeInfo:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getTVDBEpisodeInfo = mocker.patch(
            'mediaviewer.models.posterfile.getTVDBEpisodeInfo')

        self.fake_data = {'still_path': 'test_path',
                          'overview': 'test_overview',
                          'name': 'test_name'}
        self.tvdb_id = 123

        self.test_obj = PosterFile()

    def test_got_tvinfo(self):
        self.mock_getTVDBEpisodeInfo.return_value = self.fake_data

        expected = None
        actual = self.test_obj._tvdb_episode_info(self.tvdb_id)

        assert expected == actual
        self.mock_getTVDBEpisodeInfo.assert_called_once_with(
            123,
            self.test_obj.season,
            self.test_obj.episode)
        assert 'test_path' == self.test_obj.poster_url
        assert 'test_overview' == self.test_obj.extendedplot
        assert 'test_name' == self.test_obj.episodename

    def test_no_tvinfo(self):
        self.mock_getTVDBEpisodeInfo.return_value = None

        expected = None
        actual = self.test_obj._tvdb_episode_info(self.tvdb_id)

        assert expected == actual
        self.mock_getTVDBEpisodeInfo.assert_called_once_with(
            123,
            self.test_obj.season,
            self.test_obj.episode)
        assert self.test_obj.poster_url is None
        assert '' == self.test_obj.extendedplot
        assert self.test_obj.episodename is None


@pytest.mark.django_db
class TestAssignTVDBInfo:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_searchTVDBByName = mocker.patch(
            'mediaviewer.models.posterfile.searchTVDBByName')

        self.mock_tvdb_episode_info = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._tvdb_episode_info')

        self.fake_data = {
            'results': [
                {'id': 123},
            ]
        }
        self.mock_searchTVDBByName.return_value = self.fake_data

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.movie_path = Path.objects.create(localpathstr='movie.local.path',
                                              remotepathstr='movie.remote.path',
                                              is_movie=True)
        self.movie_file = File.new('new.file.mp4',
                                   self.movie_path)

        self.test_obj = PosterFile()

    def test_movie_file(self):
        self.test_obj.file = self.movie_file

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        assert expected == actual
        assert not self.mock_searchTVDBByName.called
        assert not self.mock_tvdb_episode_info.called

    def test_movie_path(self):
        self.test_obj.path = self.movie_path

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        assert expected == actual
        assert not self.mock_searchTVDBByName.called
        assert not self.mock_tvdb_episode_info.called

    def test_tv_path(self):
        self.test_obj.path = self.tv_path

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        assert expected == actual
        assert not self.mock_searchTVDBByName.called
        assert not self.mock_tvdb_episode_info.called

    def test_path_has_tvdb_id(self):
        self.tv_path.tvdb_id = 123
        self.test_obj.file = self.tv_file

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        assert expected == actual
        assert not self.mock_searchTVDBByName.called
        self.mock_tvdb_episode_info.assert_called_once_with(123)

    def test_path_has_no_tvdb_id(self):
        self.test_obj.file = self.tv_file

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        assert expected == actual
        assert self.tv_path.tvdb_id == 123
        self.mock_searchTVDBByName.assert_called_once_with(
            self.tv_file.searchString())
        self.mock_tvdb_episode_info.assert_called_once_with(123)

    def test_badly_formatted_tvinfo(self):
        self.mock_searchTVDBByName.return_value = {}

        expected = None
        actual = self.test_obj._assign_tvdb_info()

        assert expected == actual
        assert not self.mock_searchTVDBByName.called
        assert not self.mock_tvdb_episode_info.called


@pytest.mark.django_db
class TestPopulatePosterData:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getIMDBData = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._getIMDBData')

        self.mock_download_poster = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._download_poster')

        self.test_obj = PosterFile()

    def test_valid(self):
        expected = None
        actual = self.test_obj._populate_poster_data()

        assert expected == actual
        self.mock_getIMDBData.assert_called_once_with()
        self.mock_download_poster.assert_called_once_with()


@pytest.mark.django_db
class TestDownloadPoster:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_saveImageToDisk = mocker.patch(
            'mediaviewer.models.posterfile.saveImageToDisk')

        self.test_obj = PosterFile()
        self.test_obj.poster_url = '/test_poster_url'

    def test_missing_poster_url(self):
        self.test_obj.poster_url = None

        expected = None
        actual = self.test_obj._download_poster()

        assert expected == actual
        assert not self.mock_saveImageToDisk.called
        assert self.test_obj.image is None

    def test_valid(self):
        expected = None
        actual = self.test_obj._download_poster()

        assert expected == actual
        self.mock_saveImageToDisk.assert_called_once_with(
            self.test_obj.poster_url,
            self.test_obj.image)
        assert 'test_poster_url' == self.test_obj.image


@pytest.mark.django_db
class TestStorePlot:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = PosterFile()

    def test_has_plot(self):
        test_data = {'Plot': 'test_plot'}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert 'test_plot' == self.test_obj.plot

    def test_has_overview(self):
        test_data = {'overview': 'test_overview'}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert 'test_overview' == self.test_obj.plot

    def test_has_multiple_results(self):
        test_data = {'results': [
            {'overview': 'test_results_overview'},
        ]}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert 'test_results_overview' == self.test_obj.plot

    def test_plot_undefined(self):
        test_data = {'Plot': 'undefined'}

        expected = None
        actual = self.test_obj._store_plot(test_data)

        assert expected == actual
        assert self.test_obj.plot is None


@pytest.mark.django_db
class TestStoreGenres:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_tvdbConfig = mocker.patch(
            'mediaviewer.models.posterfile.tvdbConfig')

        self.mock_tvdbConfig.genres = {
            123: 'test_genre'}

        self.test_obj = PosterFile()
        self.test_obj.save()

    def test_has_results(self):
        imdb_data = {
            'results': [
                {'genre_ids': [123]},
            ],
        }

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        assert expected == actual
        assert 'Test_Genre' == self.test_obj.genres.all()[0].genre

    def test_has_genre_ids(self):
        imdb_data = {'genre_ids': [123]}

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        assert expected == actual
        assert 'Test_Genre' == self.test_obj.genres.all()[0].genre

    def test_has_genres(self):
        imdb_data = {'genres': [
            {'name': 'test_genre'},
        ]}

        expected = None
        actual = self.test_obj._store_genres(imdb_data)

        assert expected == actual
        assert 'Test_Genre' == self.test_obj.genres.all()[0].genre


@pytest.mark.django_db
class TestStoreRating:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = PosterFile()

    def test_has_imdb_rating(self):
        test_data = {
            'imdbRating': 'test_rating',
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        assert expected == actual
        assert 'test_rating' == self.test_obj.rating

    def test_has_vote_average(self):
        test_data = {
            'vote_average': 'test_rating',
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        assert expected == actual
        assert 'test_rating' == self.test_obj.rating

    def test_undefined(self):
        test_data = {
            'vote_average': 'undefined',
        }

        expected = None
        actual = self.test_obj._store_rating(test_data)

        assert expected == actual
        assert self.test_obj.rating is None


@pytest.mark.django_db
class TestStoreTagline:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_obj = PosterFile()

    def test_has_vote_average(self):
        test_data = {
            'tagline': 'test_tagline',
        }

        expected = None
        actual = self.test_obj._store_tagline(test_data)

        assert expected == actual
        assert 'test_tagline' == self.test_obj.tagline

    def test_undefined(self):
        test_data = {
            'tagline': 'undefined',
        }

        expected = None
        actual = self.test_obj._store_tagline(test_data)

        assert expected == actual
        assert self.test_obj.tagline is None


@pytest.mark.django_db
class TestStoreExtendedInfo:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getExtendedInfo = mocker.patch(
            'mediaviewer.models.posterfile.getExtendedInfo')

        self.mock_store_rating = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_rating')

        self.mock_store_tagline = mocker.patch(
            'mediaviewer.models.posterfile.PosterFile._store_tagline')

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        self.test_obj = PosterFile()
        self.test_obj.tmdb_id = 123
        self.test_obj.file = self.tv_file

    def test_valid(self):
        expected = None
        actual = self.test_obj._store_extended_info()

        assert expected == actual
        self.mock_getExtendedInfo.assert_called_once_with(
            123,
            isMovie=False)
        self.mock_store_rating.assert_called_once_with(
            self.mock_getExtendedInfo.return_value)
        self.mock_store_tagline.assert_called_once_with(
            self.mock_getExtendedInfo.return_value)


class TestStoreRated:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_data = {'Rated': 'test_rated'}

        self.test_obj = PosterFile()

    def test_has_rated(self):
        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        assert expected == actual
        assert 'test_rated' == self.test_obj.rated

    def test_no_rated(self):
        self.test_data = {}

        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        assert expected == actual
        assert self.test_obj.rated is None

    def test_undefined(self):
        self.test_data = {'Rated': 'undefined'}

        expected = None
        actual = self.test_obj._store_rated(self.test_data)

        assert expected == actual
        assert self.test_obj.rated is None
