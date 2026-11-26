import hashlib
from urllib.parse import parse_qs, urlsplit

import boto3
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
            "s3ApiUrl": "https://s3.us-east-005.backblazeb2.com",
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
    "s3ApiUrl": "https://s3.us-east-005.backblazeb2.com",
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
        assert auth["s3ApiUrl"] == "https://s3.us-east-005.backblazeb2.com"
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

    def test_presigned_url_uses_refreshed_s3_endpoint(self, mocker, settings):
        settings.B2_PRESIGNED_URL_EXPIRY = 1234
        client = B2Client("key-id", "key")
        renewed_response = {
            **AUTHORIZE_RESPONSE,
            "authorizationToken": "renewed-account-token",
            "apiInfo": {
                "storageApi": {
                    **AUTHORIZE_RESPONSE["apiInfo"]["storageApi"],
                    "s3ApiUrl": "https://s3.us-west-004.backblazeb2.com",
                },
            },
        }
        mock_get = mocker.patch("mediaviewer.b2.requests.get")
        mock_get.side_effect = [
            FakeResponse(AUTHORIZE_RESPONSE),
            FakeResponse(renewed_response),
        ]
        mocker.patch("time.monotonic", side_effect=[100, 3700, 3700, 3700])
        client._authorize()
        url = urlsplit(client.generate_presigned_url("mybucket", "key/foo.mp4"))

        assert url.netloc == "s3.us-west-004.backblazeb2.com"
        assert (
            "/us-west-004/s3/aws4_request" in parse_qs(url.query)["X-Amz-Credential"][0]
        )

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
    def test_signs_s3_get_without_native_download_authorization(self, mocker, settings):
        settings.B2_PRESIGNED_URL_EXPIRY = 14400
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.return_value = FakeResponse({"authorizationToken": "download-token"})

        url = urlsplit(client.generate_presigned_url("mybucket", "key/foo.mp4"))
        query = parse_qs(url.query)

        assert url.scheme == "https"
        assert url.netloc == "s3.us-east-005.backblazeb2.com"
        assert url.path == "/mybucket/key/foo.mp4"
        assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
        assert query["X-Amz-Credential"][0].startswith("key-id/")
        assert "/us-east-005/s3/aws4_request" in query["X-Amz-Credential"][0]
        assert query["X-Amz-Expires"] == ["14400"]
        assert query["X-Amz-SignedHeaders"] == ["host"]
        assert query["X-Amz-Signature"]
        assert "Authorization" not in query
        mock_post.assert_not_called()

    def test_generate_presigned_url(self, mocker, settings):
        settings.B2_PRESIGNED_URL_EXPIRY = 1234
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        url = client.generate_presigned_url("mybucket", "key/foo.mp4")

        assert parse_qs(urlsplit(url).query)["X-Amz-Expires"] == ["1234"]

    def test_generate_presigned_url_encodes_spaces(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        url = client.generate_presigned_url("mybucket", "movies/Movie Name/foo.mp4")

        assert urlsplit(url).path == "/mybucket/movies/Movie%20Name/foo.mp4"

    def test_generate_presigned_url_with_custom_expiry(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        url = client.generate_presigned_url("mybucket", "key/foo.mp4", expires_in=60)

        assert parse_qs(urlsplit(url).query)["X-Amz-Expires"] == ["60"]

    def test_generate_presigned_url_signs_content_disposition(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        disposition = 'inline; filename="Show.S01E02.mkv"'

        url = client.generate_presigned_url(
            "mybucket", "key/foo.mp4", content_disposition=disposition
        )

        query = parse_qs(urlsplit(url).query)
        assert query["response-content-disposition"] == [disposition]
        assert "b2ContentDisposition" not in query
        assert query["X-Amz-Signature"]

    @pytest.mark.parametrize(
        ("key", "path"),
        [
            ("nested/000/001/234/video.mp4", "/mybucket/nested/000/001/234/video.mp4"),
            ("a+b%20?#.mp4", "/mybucket/a%2Bb%2520%3F%23.mp4"),
            (
                "日本語/épisode.mp4",
                "/mybucket/%E6%97%A5%E6%9C%AC%E8%AA%9E/%C3%A9pisode.mp4",
            ),
            ("/leading//slashes.mp4", "/mybucket//leading//slashes.mp4"),
        ],
    )
    def test_preserves_exact_object_key(self, mocker, key, path):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)

        assert urlsplit(client.generate_presigned_url("mybucket", key)).path == path

    @pytest.mark.parametrize("expiry", [0, -1, 604801, True, 1.5, "60"])
    def test_rejects_invalid_expiry(self, mocker, expiry):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)

        with pytest.raises(B2Error, match="expiry must be between"):
            client.generate_presigned_url("mybucket", "key", expires_in=expiry)

    @pytest.mark.parametrize(
        "endpoint",
        [None, "", "http://s3.us-east-005.backblazeb2.com", "https://s3.example.com"],
    )
    def test_rejects_missing_or_untrusted_endpoint(self, mocker, endpoint):
        client = B2Client("key-id", "key")
        mocker.patch.object(
            client, "_authorize", return_value={**AUTH, "s3ApiUrl": endpoint}
        )

        with pytest.raises(B2Error, match="invalid S3 endpoint"):
            client.generate_presigned_url("mybucket", "key")

    def test_reuses_client_with_explicit_b2_credentials(self, mocker, monkeypatch):
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "unrelated-aws-key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "unrelated-aws-secret")
        monkeypatch.setenv("AWS_SESSION_TOKEN", "unrelated-session-token")
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        create_client = mocker.spy(boto3, "client")

        first = client.generate_presigned_url("mybucket", "one.mp4")
        second = client.generate_presigned_url("mybucket", "two.mp4")

        assert create_client.call_count == 1
        kwargs = create_client.call_args.kwargs
        assert kwargs["aws_access_key_id"] == "key-id"
        assert kwargs["aws_secret_access_key"] == "key"
        assert kwargs["region_name"] == "us-east-005"
        assert kwargs["config"].signature_version == "s3v4"
        assert kwargs["config"].s3 == {"addressing_style": "path"}
        for url in (first, second):
            query = parse_qs(urlsplit(url).query)
            assert query["X-Amz-Credential"][0].startswith("key-id/")
            assert "X-Amz-Security-Token" not in query

    def test_sdk_signing_error_is_safe(self, mocker):
        from botocore.exceptions import ParamValidationError

        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mocker.patch(
            "mediaviewer.b2.boto3.client",
            side_effect=ParamValidationError(report="private signing details"),
        )

        with pytest.raises(B2Error, match="^B2 S3 download URL signing failed$"):
            client.generate_presigned_url("mybucket", "key")

    def test_recreates_client_when_authorized_endpoint_changes(self, mocker):
        client = B2Client("key-id", "key")
        authorize = mocker.patch.object(client, "_authorize", return_value=AUTH)
        client.generate_presigned_url("mybucket", "one.mp4")
        original_client = client._s3_client
        authorize.return_value = {
            **AUTH,
            "s3ApiUrl": "https://s3.us-west-004.backblazeb2.com",
        }

        url = urlsplit(client.generate_presigned_url("mybucket", "two.mp4"))

        assert client._s3_client is not original_client
        assert url.netloc == "s3.us-west-004.backblazeb2.com"
        assert (
            "/us-west-004/s3/aws4_request" in parse_qs(url.query)["X-Amz-Credential"][0]
        )

    @pytest.mark.parametrize("expiry", [1, 604800])
    def test_accepts_expiry_boundaries(self, mocker, expiry):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)

        url = client.generate_presigned_url("mybucket", "key", expires_in=expiry)

        assert parse_qs(urlsplit(url).query)["X-Amz-Expires"] == [str(expiry)]

    def test_keeps_dotted_bucket_in_path(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(
            client, "_authorize", return_value={**AUTH, "buckets": {"my.bucket": "id"}}
        )

        url = urlsplit(client.generate_presigned_url("my.bucket", "key"))

        assert url.netloc == "s3.us-east-005.backblazeb2.com"
        assert url.path == "/my.bucket/key"

    def test_rejects_bucket_outside_authorized_scope(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        create_client = mocker.patch("mediaviewer.b2.boto3.client")

        with pytest.raises(B2Error, match="not accessible"):
            client.generate_presigned_url("other-bucket", "key")

        create_client.assert_not_called()


class TestB2ClientDelete:
    def test_repeated_listing_cursor_raises_without_deleting(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.side_effect = [
            FakeResponse(
                {
                    "files": [{"fileName": "key", "fileId": "v1", "action": "upload"}],
                    "nextFileName": "key",
                    "nextFileId": "v1",
                }
            ),
            FakeResponse(
                {
                    "files": [{"fileName": "key", "fileId": "v2", "action": "upload"}],
                    "nextFileName": "key",
                    "nextFileId": "v1",
                }
            ),
        ]

        with pytest.raises(B2Error, match="repeated its pagination cursor"):
            client.delete_file("mybucket", "key")

        assert mock_post.call_count == 2
        assert all(
            "b2_list_file_versions" in call.args[0] for call in mock_post.call_args_list
        )

    def test_delete_file_collects_all_matching_versions_before_deleting(self, mocker):
        client = B2Client("key-id", "key")
        mocker.patch.object(client, "_authorize", return_value=AUTH)
        mock_post = mocker.patch("mediaviewer.b2.requests.post")
        mock_post.side_effect = [
            FakeResponse(
                {
                    "files": [
                        {
                            "fileName": "folder/movie.mp4",
                            "fileId": "v1",
                            "action": "upload",
                        },
                        {
                            "fileName": "folder/movie.mp4",
                            "fileId": "v2",
                            "action": "hide",
                        },
                        {
                            "fileName": "folder/movie.mp4",
                            "fileId": "unfinished",
                            "action": "start",
                        },
                        {
                            "fileName": "folder/movie.mp4.extra",
                            "fileId": "neighbor",
                            "action": "upload",
                        },
                    ],
                    "nextFileName": "folder/movie.mp4",
                    "nextFileId": "v2",
                }
            ),
            FakeResponse(
                {
                    "files": [
                        {
                            "fileName": "folder/movie.mp4",
                            "fileId": "v3",
                            "action": "upload",
                        },
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
            FakeResponse(
                {
                    "files": [{"fileName": "key", "fileId": "one", "action": "upload"}],
                    "nextFileName": "key",
                    "nextFileId": "one",
                }
            ),
            FakeResponse(
                {"files": [{"fileName": "key", "fileId": "two", "action": "upload"}]}
            ),
            FakeResponse({}),
            FakeResponse({}),
        ]

        client.delete_file("mybucket", "key")

        assert [
            call.kwargs["json"]["fileId"] for call in mock_post.call_args_list[2:]
        ] == [
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
                    FakeResponse(
                        {
                            "files": [
                                {"fileName": "key", "fileId": "v1", "action": "upload"}
                            ]
                        }
                    ),
                    FakeResponse(status_code=403),
                ]

        with pytest.raises(RuntimeError, match="HTTP 403"):
            client.delete_file("mybucket", "key")
