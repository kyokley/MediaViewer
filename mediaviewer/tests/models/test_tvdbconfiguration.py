import mock

from django.test import TestCase

from mediaviewer.models.tvdbconfiguration import (
        getJSONData,
        TVDBConfiguration,
        )


class TestGetJSONData(TestCase):
    def setUp(self):
        self.get_patcher = mock.patch(
                'mediaviewer.models.tvdbconfiguration.requests.get')
        self.mock_get = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        self.sleep_patcher = mock.patch(
                'mediaviewer.models.tvdbconfiguration.time.sleep')
        self.mock_sleep = self.sleep_patcher.start()
        self.addCleanup(self.sleep_patcher.stop)

    def test_valid(self):
        expected = self.mock_get.return_value.json.return_value
        actual = getJSONData('test_url')

        self.assertEqual(expected, actual)

    def test_not_rate_limited(self):
        self.mock_get.return_value.headers = {
                'X-RateLimit-Remaining': '10',
                'X-RateLimit-Limit': '40',
                }

        expected = self.mock_get.return_value.json.return_value
        actual = getJSONData('test_url')

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_sleep.called)

    def test_rate_limited(self):
        self.mock_get.return_value.headers = {
                'X-RateLimit-Remaining': '3',
                'X-RateLimit-Limit': '40',
                }

        expected = self.mock_get.return_value.json.return_value
        actual = getJSONData('test_url')

        self.assertEqual(expected, actual)
        self.mock_sleep.assert_called_once_with(1)


class TestTVDBConfigurationInit(TestCase):
    def setUp(self):
        self.getTVDBConfiguration_patcher = mock.patch(
                'mediaviewer.models.tvdbconfiguration.TVDBConfiguration._getTVDBConfiguration')
        self.mock_getTVDBConfiguration = (
                self.getTVDBConfiguration_patcher.start())
        self.addCleanup(self.getTVDBConfiguration_patcher.stop)

        self.getTVDBGenres_patcher = mock.patch(
                'mediaviewer.models.tvdbconfiguration.TVDBConfiguration._getTVDBGenres')
        self.mock_getTVDBGenres = self.getTVDBGenres_patcher.start()
        self.addCleanup(self.getTVDBGenres_patcher.stop)

        self.fake_config_data = {
                'images': {
                    'secure_base_url': 'test_base_url',
                    'still_sizes': [1, 2, 3],
                    }
                }

        self.mock_getTVDBConfiguration.return_value = self.fake_config_data

    def test_valid(self):
        test_obj = TVDBConfiguration()

        self.assertEqual(test_obj.url, 'test_base_url')
        self.assertEqual(test_obj.poster_size, 'w500')
        self.assertEqual(test_obj.still_size, 3)
        self.assertEqual(test_obj.connected, True)
        self.assertEqual(test_obj.genres, self.mock_getTVDBGenres.return_value)

    def test_got_bad_config_data(self):
        self.mock_getTVDBConfiguration.return_value = None

        test_obj = TVDBConfiguration()

        self.assertEqual(test_obj.url, '')
        self.assertEqual(test_obj.poster_size, '')
        self.assertEqual(test_obj.still_size, '')
        self.assertEqual(test_obj.connected, False)
        self.assertEqual(test_obj.genres, {})

    def test_got_bad_genre_data(self):
        self.mock_getTVDBGenres.return_value = None

        test_obj = TVDBConfiguration()

        self.assertEqual(test_obj.url, '')
        self.assertEqual(test_obj.poster_size, '')
        self.assertEqual(test_obj.still_size, '')
        self.assertEqual(test_obj.connected, False)
        self.assertEqual(test_obj.genres, {})
