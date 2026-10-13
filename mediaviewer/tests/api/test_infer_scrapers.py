import pytest


@pytest.mark.django_db
class TestInferScrapers:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_user):
        self.client = client
        self.user = create_user(is_staff=True)
        self.client.force_login(self.user)
        self.url = "/mediaviewer/api/inferscrapers/"

    def test_get_returns_media_path_uri(self, mocker, create_tv):
        tv = create_tv(name="Example Show")
        media_path = tv.media_path
        media_path._path = "b2://bucket/tv/Example Show/"
        media_path.save()
        infer = mocker.patch(
            "mediaviewer.models.filenamescrapeformat.FilenameScrapeFormat.tv_for_filename",
            return_value=media_path,
        )

        response = self.client.get(self.url, {"title": "Example.Show.S01E02.mkv"})

        assert response.status_code == 200
        assert response.json() == {"path": "b2://bucket/tv/Example Show/"}
        infer.assert_called_once_with("Example.Show.S01E02.mkv")

    def test_get_returns_empty_path_when_no_match(self, mocker):
        infer = mocker.patch(
            "mediaviewer.models.filenamescrapeformat.FilenameScrapeFormat.tv_for_filename",
            return_value=None,
        )

        response = self.client.get(self.url, {"title": "Unknown.Show.S01E02.mkv"})

        assert response.status_code == 200
        assert response.json() == {"path": ""}
        infer.assert_called_once_with("Unknown.Show.S01E02.mkv")

    def test_get_runs_tvdb_inference_and_creates_linked_b2_path(
        self, mocker, create_tv, settings
    ):
        tv = create_tv(name="Example Show")
        local_path = tv.media_path
        local_path._path = "/library/Example Show"
        local_path.save()
        settings.THETVDB_API_KEY = "test-api-key"
        settings.THETVDB_PIN = "test-pin"
        settings.B2_BUCKET_NAME = "configured-bucket"
        settings.B2_NAME_PREFIX = "tv/"

        login_response = mocker.Mock()
        login_response.json.return_value = {"data": {"token": "test-token"}}
        search_response = mocker.Mock()
        search_response.json.return_value = {
            "data": [
                {
                    "id": "series-1",
                    "name": "Example Show",
                    "aliases": [],
                    "type": "series",
                }
            ]
        }
        login = mocker.patch(
            "mediaviewer.thetvdb.requests.post", return_value=login_response
        )
        search = mocker.patch(
            "mediaviewer.thetvdb.requests.get", return_value=search_response
        )

        response = self.client.get(self.url, {"title": "Example.Show.S01E02.mkv"})

        expected_uri = "b2://configured-bucket/tv/Example Show/"
        assert response.status_code == 200
        assert response.json() == {"path": expected_uri}
        login.assert_called_once_with(
            "https://api4.thetvdb.com/v4/login",
            json={"apikey": "test-api-key", "pin": "test-pin"},
            timeout=settings.REQUEST_TIMEOUT,
        )
        search.assert_called_once_with(
            "https://api4.thetvdb.com/v4/search",
            params={"query": "Example Show", "type": "series"},
            headers={"Authorization": "Bearer test-token"},
            timeout=settings.REQUEST_TIMEOUT,
        )
        local_path.refresh_from_db()
        assert local_path._path == "/library/Example Show"
        created_path = tv.mediapath_set.get(_path=expected_uri)
        assert created_path.tv_id == tv.pk

    def test_get_without_title_preserves_missing_input_failure(self):
        with pytest.raises(KeyError):
            self.client.get(self.url)
