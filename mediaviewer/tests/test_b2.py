import hashlib

import pytest

from mediaviewer.b2 import B2Client, B2Error, get_b2_client


class FakeResponse:
    def __init__(self, data=None, status_code=200):
        self._data = data or {}
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


AUTHORIZE_RESPONSE = {
    "authorizationToken": "account-token",
    "apiInfo": {
        "storageApi": {
            "apiUrl": "https://api123.backblazeb2.com",
            "downloadUrl": "https://f123.backblazeb2.com",
            "allowed": {
                "buckets": [{"id": "bucket-id-1", "name": "mybucket"}],
            },
        }
    },
}

AUTH = {
    "authorizationToken": "account-token",
    "apiUrl": "https://api123.backblazeb2.com",
    "downloadUrl": "https://f123.backblazeb2.com",
    "buckets": {"mybucket": "bucket-id-1"},
}


class TestB2ClientAuthorize:
    def test_authorize_uses_basic_auth(self, mocker):
        client = B2Client("key-id", "key")
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.return_value = FakeResponse(AUTHORIZE_RESPONSE)

        auth = client._authorize()

        mock_get.assert_called_once_with(
            "https://api.backblazeb2.com/b2api/v4/b2_authorize_account",
            auth=("key-id", "key"),
            timeout=30,
        )
        assert auth["authorizationToken"] == "account-token"
        assert auth["apiUrl"] == "https://api123.backblazeb2.com"
        assert auth["downloadUrl"] == "https://f123.backblazeb2.com"
        assert auth["buckets"] == {"mybucket": "bucket-id-1"}

    def test_authorize_is_cached(self, mocker):
        client = B2Client("key-id", "key")
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.return_value = FakeResponse(AUTHORIZE_RESPONSE)

        client._authorize()
        client._authorize()

        assert mock_get.call_count == 1


class TestGetB2Client:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_b2_client.cache_clear()
        yield
        get_b2_client.cache_clear()

    def test_requires_credentials_together(self, settings, mocker):
        settings.B2_APPLICATION_KEY_ID = "key"
        settings.B2_APPLICATION_KEY = ""
        mocker.patch("mediaviewer.b2.B2Client")

        with pytest.raises(ValueError, match="must be set together"):
            get_b2_client()

    def test_accepts_both_credentials(self, settings, mocker):
        settings.B2_APPLICATION_KEY_ID = "key"
        settings.B2_APPLICATION_KEY = "secret"
        mock_client_cls = mocker.patch("mediaviewer.b2.B2Client")

        get_b2_client()

        mock_client_cls.assert_called_once_with(
            application_key_id="key",
            application_key="secret",
            api_url=settings.B2_API_URL,
        )


class TestB2ClientUpload:
    def test_upload_single_file(self, mocker, tmp_path):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.return_value = FakeResponse(
            {
                "bucketId": "bucket-id-1",
                "uploadUrl": "https://upload.example.com",
                "authorizationToken": "upload-token",
            }
        )
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"fileId": "file-1"})

        local_file = tmp_path / "foo.mp4"
        local_file.write_bytes(b"data")

        client.upload_file(local_file, "mybucket", "key/foo.mp4")

        mock_get.assert_called_once_with(
            "https://api123.backblazeb2.com/b2api/v4/b2_get_upload_url",
            params={"bucketId": "bucket-id-1"},
            headers={"Authorization": "account-token"},
            timeout=30,
        )
        call = mock_post.call_args
        assert call.args[0] == "https://upload.example.com"
        headers = call.kwargs["headers"]
        assert headers["Authorization"] == "upload-token"
        assert headers["X-Bz-File-Name"] == "key/foo.mp4"
        assert headers["Content-Type"] == "video/mp4"
        assert headers["Content-Length"] == "4"
        assert headers["X-Bz-Content-Sha1"] == hashlib.sha1(b"data").hexdigest()

    def test_upload_file_percent_encodes_name(self, mocker, tmp_path):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.return_value = FakeResponse(
            {
                "uploadUrl": "https://upload.example.com",
                "authorizationToken": "upload-token",
            }
        )
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({})

        local_file = tmp_path / "foo.mp4"
        local_file.write_bytes(b"data")

        client.upload_file(local_file, "mybucket", "movies/Movie Name/foo.mp4")

        headers = mock_post.call_args.kwargs["headers"]
        assert headers["X-Bz-File-Name"] == "movies/Movie%20Name/foo.mp4"

    def test_upload_unknown_bucket_raises(self, mocker, tmp_path):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        local_file = tmp_path / "foo.mp4"
        local_file.write_bytes(b"data")

        with pytest.raises(B2Error, match="not accessible"):
            client.upload_file(local_file, "otherbucket", "key/foo.mp4")

    def test_upload_large_file(self, mocker, tmp_path, monkeypatch):
        monkeypatch.setattr("mediaviewer.b2.MAX_SINGLE_UPLOAD_SIZE", 1)
        monkeypatch.setattr("mediaviewer.b2.LARGE_FILE_PART_SIZE", 2)
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.return_value = FakeResponse(
            {
                "fileId": "large-file-id",
                "uploadUrl": "https://part-upload.example.com",
                "authorizationToken": "part-token",
            }
        )
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"fileId": "large-file-id"})

        local_file = tmp_path / "big.mp4"
        local_file.write_bytes(b"abcdef")

        client.upload_file(local_file, "mybucket", "key/big.mp4")

        start_call = mock_post.call_args_list[0]
        assert (
            start_call.args[0]
            == "https://api123.backblazeb2.com/b2api/v4/b2_start_large_file"
        )
        assert start_call.kwargs["json"] == {
            "bucketId": "bucket-id-1",
            "fileName": "key/big.mp4",
            "contentType": "video/mp4",
        }

        part_url_call = mock_get.call_args
        assert (
            part_url_call.args[0]
            == "https://api123.backblazeb2.com/b2api/v4/b2_get_upload_part_url"
        )
        assert part_url_call.kwargs["params"] == {"fileId": "large-file-id"}

        part_calls = mock_post.call_args_list[1:4]
        assert len(part_calls) == 3
        for i, call in enumerate(part_calls, start=1):
            assert call.args[0] == "https://part-upload.example.com"
            assert call.kwargs["headers"]["Authorization"] == "part-token"
            assert call.kwargs["headers"]["X-Bz-Part-Number"] == str(i)
            assert call.kwargs["headers"]["Content-Length"] == "2"

        finish_call = mock_post.call_args_list[4]
        assert (
            finish_call.args[0]
            == "https://api123.backblazeb2.com/b2api/v4/b2_finish_large_file"
        )
        assert finish_call.kwargs["json"]["fileId"] == "large-file-id"
        sha1s = finish_call.kwargs["json"]["partSha1Array"]
        assert len(sha1s) == 3
        assert sha1s == [
            hashlib.sha1(b"ab").hexdigest(),
            hashlib.sha1(b"cd").hexdigest(),
            hashlib.sha1(b"ef").hexdigest(),
        ]


class TestB2ClientGeneratePresignedUrl:
    def test_generate_presigned_url(self, mocker, settings):
        settings.B2_PRESIGNED_URL_EXPIRY = 1234
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse(
            {
                "bucketId": "bucket-id-1",
                "fileNamePrefix": "key/foo.mp4",
                "authorizationToken": "download-token",
            }
        )

        url = client.generate_presigned_url("mybucket", "key/foo.mp4")

        assert (
            url
            == "https://f123.backblazeb2.com/file/mybucket/key/foo.mp4?Authorization=download-token"
        )
        mock_post.assert_called_once_with(
            "https://api123.backblazeb2.com/b2api/v4/b2_get_download_authorization",
            json={
                "bucketId": "bucket-id-1",
                "fileNamePrefix": "key/foo.mp4",
                "validDurationInSeconds": 1234,
            },
            headers={"Authorization": "account-token"},
            timeout=30,
        )

    def test_generate_presigned_url_encodes_spaces(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"authorizationToken": "download-token"})

        url = client.generate_presigned_url("mybucket", "movies/Movie Name/foo.mp4")

        assert (
            url
            == "https://f123.backblazeb2.com/file/mybucket/movies/Movie%20Name/foo.mp4?Authorization=download-token"
        )

    def test_generate_presigned_url_with_custom_expiry(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"authorizationToken": "download-token"})

        client.generate_presigned_url("mybucket", "key/foo.mp4", expires_in=60)

        assert mock_post.call_args.kwargs["json"]["validDurationInSeconds"] == 60
