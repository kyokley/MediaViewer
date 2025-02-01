import pytest

from django.test import override_settings

from mediaviewer.models.tvdbconfiguration import TVDBConfiguration, getJSONData


class TestGetJSONData:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_get = mocker.patch(
            "mediaviewer.models.tvdbconfiguration.requests.get"
        )

        self.mock_sleep = mocker.patch(
            "mediaviewer.models.tvdbconfiguration.time.sleep"
        )

    def test_valid(self):
        expected = self.mock_get.return_value.json.return_value
        actual = getJSONData("test_url")

        assert expected == actual

    def test_not_rate_limited(self):
        self.mock_get.return_value.headers = {
            "X-RateLimit-Remaining": "12",
            "X-RateLimit-Limit": "40",
        }

        expected = self.mock_get.return_value.json.return_value
        actual = getJSONData("test_url")

        assert expected == actual
        assert not self.mock_sleep.called

    def test_rate_limited(self):
        self.mock_get.return_value.headers = {
            "X-RateLimit-Remaining": "3",
            "X-RateLimit-Limit": "40",
        }

        expected = self.mock_get.return_value.json.return_value
        actual = getJSONData("test_url")

        assert expected == actual
        self.mock_sleep.assert_called_once_with(1)


class TestTVDBConfigurationInit:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_getTVDBConfiguration = mocker.patch(
            "mediaviewer.models.tvdbconfiguration.TVDBConfiguration._getTVDBConfiguration"
        )

        self.mock_getTVDBGenres = mocker.patch(
            "mediaviewer.models.tvdbconfiguration.TVDBConfiguration._getTVDBGenres"
        )

        self.fake_config_data = {
            "images": {
                "secure_base_url": "test_base_url",
                "still_sizes": [1, 2, 3],
            }
        }

        self.mock_getTVDBConfiguration.return_value = self.fake_config_data

    @override_settings(SKIP_LOADING_TVDB_CONFIG=False)
    def test_valid(self):
        test_obj = TVDBConfiguration()

        assert test_obj.url == "test_base_url"
        assert test_obj.poster_size == "w500"
        assert test_obj.still_size == 3
        assert test_obj.connected
        assert test_obj.genres == self.mock_getTVDBGenres.return_value

    @override_settings(SKIP_LOADING_TVDB_CONFIG=False)
    def test_got_bad_config_data(self):
        self.mock_getTVDBConfiguration.return_value = None

        with pytest.raises(Exception):
            TVDBConfiguration()

    @override_settings(SKIP_LOADING_TVDB_CONFIG=False)
    def test_got_bad_genre_data(self):
        self.mock_getTVDBGenres.return_value = None

        with pytest.raises(Exception):
            TVDBConfiguration()
