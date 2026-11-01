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

    def test_authorize_reuses_cache_before_one_hour(self, mocker):
        client = B2Client("key-id", "key")
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.return_value = FakeResponse(AUTHORIZE_RESPONSE)
        mock_clock = mocker.patch("time.monotonic", side_effect=[100, 3699])

        first_auth = client._authorize()
        second_auth = client._authorize()

        assert first_auth is second_auth
        assert mock_get.call_count == 1
        assert mock_clock.call_count == 2

    @pytest.mark.parametrize("elapsed", [3600, 3601])
    def test_authorize_refreshes_at_or_after_one_hour(self, mocker, elapsed):
        client = B2Client("key-id", "key")
        renewed_response = {
            **AUTHORIZE_RESPONSE,
            "authorizationToken": "renewed-account-token",
        }
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.side_effect = [
            FakeResponse(AUTHORIZE_RESPONSE),
            FakeResponse(renewed_response),
        ]
        mocker.patch("time.monotonic", side_effect=[100, 100 + elapsed, 100 + elapsed])

        client._authorize()
        renewed_auth = client._authorize()

        assert mock_get.call_count == 2
        assert renewed_auth["authorizationToken"] == "renewed-account-token"

    def test_presigned_url_uses_renewed_account_token(self, mocker, settings):
        settings.B2_PRESIGNED_URL_EXPIRY = 1234
        client = B2Client("key-id", "key")
        renewed_response = {
            **AUTHORIZE_RESPONSE,
            "authorizationToken": "renewed-account-token",
        }
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.side_effect = [
            FakeResponse(AUTHORIZE_RESPONSE),
            FakeResponse(renewed_response),
        ]
        mocker.patch("time.monotonic", side_effect=[100, 3700, 3700, 3700])
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"authorizationToken": "download-token"})

        client._authorize()
        client.generate_presigned_url("mybucket", "key/foo.mp4")

        assert mock_post.call_args.kwargs["headers"] == {
            "Authorization": "renewed-account-token"
        }

    def test_failed_authorization_refresh_is_retried(self, mocker):
        client = B2Client("key-id", "key")
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.side_effect = [
            FakeResponse(AUTHORIZE_RESPONSE),
            FakeResponse(status_code=500),
            FakeResponse({**AUTHORIZE_RESPONSE, "authorizationToken": "retried-token"}),
        ]
        mocker.patch("time.monotonic", side_effect=[100, 3700, 3701, 3701])

        client._authorize()
        with pytest.raises(RuntimeError, match="HTTP 500"):
            client._authorize()
        retried_auth = client._authorize()

        assert mock_get.call_count == 3
        assert retried_auth["authorizationToken"] == "retried-token"


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


class TestB2ClientDelete:
    def test_repeated_listing_cursor_raises_without_deleting(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.side_effect = [
            FakeResponse({
                "files": [{"fileName": "key", "fileId": "v1", "action": "upload"}],
                "nextFileName": "key",
                "nextFileId": "v1",
            }),
            FakeResponse({
                "files": [{"fileName": "key", "fileId": "v2", "action": "upload"}],
                "nextFileName": "key",
                "nextFileId": "v1",
            }),
        ]

        with pytest.raises(B2Error, match="repeated its pagination cursor"):
            client.delete_file("mybucket", "key")

        assert mock_post.call_count == 2
        assert all("b2_list_file_versions" in call.args[0] for call in mock_post.call_args_list)

    def test_delete_file_collects_all_matching_versions_before_deleting(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.side_effect = [
            FakeResponse(
                {
                    "files": [
                        {"fileName": "folder/movie.mp4", "fileId": "v1", "action": "upload"},
                        {"fileName": "folder/movie.mp4", "fileId": "v2", "action": "hide"},
                        {"fileName": "folder/movie.mp4", "fileId": "unfinished", "action": "start"},
                        {"fileName": "folder/movie.mp4.extra", "fileId": "neighbor", "action": "upload"},
                    ],
                    "nextFileName": "folder/movie.mp4",
                    "nextFileId": "v2",
                }
            ),
            FakeResponse(
                {
                    "files": [
                        {"fileName": "folder/movie.mp4", "fileId": "v3", "action": "upload"},
                    ],
                }
            ),
            FakeResponse({}),
            FakeResponse({}),
            FakeResponse({}),
        ]

        client.delete_file("mybucket", "folder/movie.mp4")

        list_url = "https://api123.backblazeb2.com/b2api/v4/b2_list_file_versions"
        delete_url = "https://api123.backblazeb2.com/b2api/v4/b2_delete_file_version"
        assert mock_post.call_args_list[0].args == (list_url,)
        assert mock_post.call_args_list[0].kwargs == {
            "json": {
                "bucketId": "bucket-id-1",
                "prefix": "folder/movie.mp4",
                "maxFileCount": 1000,
            },
            "headers": {"Authorization": "account-token"},
            "timeout": 30,
        }
        assert mock_post.call_args_list[1].kwargs["json"] == {
            "bucketId": "bucket-id-1",
            "prefix": "folder/movie.mp4",
            "maxFileCount": 1000,
            "startFileName": "folder/movie.mp4",
            "startFileId": "v2",
        }
        delete_calls = mock_post.call_args_list[2:]
        assert [call.args[0] for call in delete_calls] == [delete_url] * 3
        assert [call.kwargs["json"] for call in delete_calls] == [
            {"fileName": "folder/movie.mp4", "fileId": "v1"},
            {"fileName": "folder/movie.mp4", "fileId": "v2"},
            {"fileName": "folder/movie.mp4", "fileId": "v3"},
        ]
        for call in delete_calls:
            assert call.kwargs == {
                "json": call.kwargs["json"],
                "headers": {"Authorization": "account-token"},
                "timeout": 30,
            }

    def test_delete_file_deletes_versions_from_all_pages(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.side_effect = [
            FakeResponse({
                "files": [{"fileName": "key", "fileId": "one", "action": "upload"}],
                "nextFileName": "key",
                "nextFileId": "one",
            }),
            FakeResponse({"files": [{"fileName": "key", "fileId": "two", "action": "upload"}]}),
            FakeResponse({}),
            FakeResponse({}),
        ]

        client.delete_file("mybucket", "key")

        assert [call.kwargs["json"]["fileId"] for call in mock_post.call_args_list[2:]] == [
            "one",
            "two",
        ]

    def test_delete_missing_key_is_noop(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"files": []})

        client.delete_file("mybucket", "missing")

        assert mock_post.call_count == 1

    def test_delete_file_unknown_bucket_raises(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")

        with pytest.raises(B2Error, match="not accessible"):
            client.delete_file("otherbucket", "key")

        mock_post.assert_not_called()

    @pytest.mark.parametrize("failure_at", ["authorize", "list", "delete"])
    def test_delete_file_propagates_http_failures(self, mocker, failure_at):
        client = B2Client("key-id", "key")
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        if failure_at == "authorize":
            mock_get.return_value = FakeResponse(status_code=403)
        else:
            mocker.patch.object(client, "_authorize", return_value=AUTH)
            if failure_at == "list":
                mock_post.return_value = FakeResponse(status_code=403)
            else:
                mock_post.side_effect = [
                    FakeResponse({
                        "files": [{"fileName": "key", "fileId": "v1", "action": "upload"}]
                    }),
                    FakeResponse(status_code=403),
                ]

        with pytest.raises(RuntimeError, match="HTTP 403"):
            client.delete_file("mybucket", "key")
