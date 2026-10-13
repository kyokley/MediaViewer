import requests
import pytest

from mediaviewer.thetvdb import parse_tv_filename, resolve_series_name


class TestParseTVFilename:
    def test_parses_title_episode_and_preserves_year(self):
        assert parse_tv_filename("The.Show_2024 - S02E03.mkv") == (
            "The Show 2024",
            2,
            3,
        )

    def test_parses_case_and_mixed_separators_from_path_basename(self):
        assert parse_tv_filename(r"C:\shows\Some-Show.s 01_e 02.mkv") == (
            "Some Show",
            1,
            2,
        )

    def test_allows_specials_season_zero(self):
        assert parse_tv_filename("Show S00E01.mkv") == ("Show", 0, 1)

    def test_rejects_missing_title_or_invalid_episode_token(self):
        for filename in (
            "S01E02.mkv",
            "Show S01.mkv",
            "Show S01E00.mkv",
            "Show S01E123.mkv",
            "Show 264.mkv",
            "Show E01.mkv",
            "",
            None,
        ):
            assert parse_tv_filename(filename) is None


def _response(payload):
    response = requests.Response()
    response.status_code = 200
    response._content = b"{}"
    response.json = lambda: payload
    return response


def _series(result_id="series-1", name="Canonical Name", aliases=None, **extra):
    return {
        "id": result_id,
        "name": name,
        "aliases": aliases or [],
        **extra,
    }


class TestResolveSeriesName:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.THETVDB_API_KEY = "test-key"
        settings.THETVDB_PIN = ""
        settings.REQUEST_TIMEOUT = 7

    def _mock_api(self, mocker, results):
        post = mocker.patch("mediaviewer.thetvdb.requests.post")
        get = mocker.patch("mediaviewer.thetvdb.requests.get")
        post.return_value = _response({"data": {"token": "test-token"}})
        get.return_value = _response({"data": results})
        return post, get

    def test_sends_login_and_search_contract_without_pin(self, mocker):
        post, get = self._mock_api(mocker, [_series(aliases=["My.Show"])])

        assert resolve_series_name("My Show") == "Canonical Name"

        post.assert_called_once_with(
            "https://api4.thetvdb.com/v4/login",
            json={"apikey": "test-key"},
            timeout=7,
        )
        get.assert_called_once_with(
            "https://api4.thetvdb.com/v4/search",
            params={"query": "My Show", "type": "series"},
            headers={"Authorization": "Bearer test-token"},
            timeout=7,
        )

    def test_includes_configured_pin(self, mocker, settings):
        settings.THETVDB_PIN = "1234"
        post, _ = self._mock_api(mocker, [_series(aliases=["My Show"])])

        assert resolve_series_name("My Show") == "Canonical Name"
        assert post.call_args.kwargs["json"] == {"apikey": "test-key", "pin": "1234"}

    def test_requires_unique_exact_name_or_alias_match(self, mocker):
        post, get = self._mock_api(
            mocker,
            [
                _series("1", "Canonical Name", aliases=["My.Show"]),
                _series("1", "Canonical Name", aliases=["My Show"]),
            ],
        )
        assert resolve_series_name("My Show") == "Canonical Name"

        get.return_value = _response(
            {
                "data": [
                    _series("1", "Canonical Name", aliases=["My Show"]),
                    _series("2", "Another Name", aliases=["My.Show"]),
                ]
            }
        )
        assert resolve_series_name("My Show") is None
        assert post.call_count == 2

    def test_exact_name_matches_without_aliases_or_with_null_aliases(self, mocker):
        _, get = self._mock_api(mocker, [{"id": "1", "name": "My Show"}])
        assert resolve_series_name("My Show") == "My Show"

        get.return_value = _response(
            {"data": [{"id": "1", "name": "My Show", "aliases": None}]}
        )
        assert resolve_series_name("My Show") == "My Show"

    def test_rejects_empty_malformed_wrong_type_and_nonmatching_results(self, mocker):
        self._mock_api(
            mocker,
            [
                _series("1", "Wrong", aliases=[]),
                _series("2", "My Show", aliases=[], type="movie"),
                {"id": "3", "name": "My Show", "aliases": "bad"},
                None,
            ],
        )
        assert resolve_series_name("My Show") is None

    def test_returns_none_for_bad_envelopes_and_token(self, mocker):
        post = mocker.patch("mediaviewer.thetvdb.requests.post")
        for payload in (
            {},
            {"data": {}},
            {"data": None},
            {"data": []},
            [],
            {"data": {"token": 42}},
        ):
            post.return_value = _response(payload)
            assert resolve_series_name("My Show") is None

        get = mocker.patch("mediaviewer.thetvdb.requests.get")
        post.return_value = _response({"data": {"token": "token"}})
        get.return_value = _response({"data": "bad"})
        assert resolve_series_name("My Show") is None

    def test_returns_none_on_http_errors(self, mocker):
        post = mocker.patch("mediaviewer.thetvdb.requests.post")
        mocker.patch("mediaviewer.thetvdb.requests.get")
        post.return_value = _response({})
        post.return_value.status_code = 401
        assert resolve_series_name("My Show") is None

        post.return_value = _response({"data": {"token": "token"}})
        get = mocker.patch("mediaviewer.thetvdb.requests.get")
        get.return_value = _response({})
        get.return_value.status_code = 500
        assert resolve_series_name("My Show") is None

    def test_returns_none_on_network_and_json_errors(self, mocker):
        post = mocker.patch("mediaviewer.thetvdb.requests.post")
        get = mocker.patch("mediaviewer.thetvdb.requests.get")
        post.side_effect = requests.Timeout("timeout")
        assert resolve_series_name("My Show") is None

        post.side_effect = None
        post.return_value = _response({"data": {"token": "token"}})
        get.side_effect = requests.ConnectionError("offline")
        assert resolve_series_name("My Show") is None

        get.side_effect = None
        get.return_value = _response({})
        get.return_value.json = lambda: (_ for _ in ()).throw(ValueError("bad json"))
        assert resolve_series_name("My Show") is None

    def test_skips_network_when_credentials_or_title_are_missing(self, mocker, settings):
        post = mocker.patch("mediaviewer.thetvdb.requests.post")
        settings.THETVDB_API_KEY = ""
        assert resolve_series_name("My Show") is None
        settings.THETVDB_API_KEY = "test-key"
        assert resolve_series_name(" ") is None
        post.assert_not_called()
