import pytest

from mediaviewer.s3 import S3Client, get_s3_client


@pytest.fixture
def mock_boto3_client(mocker):
    return mocker.patch("mediaviewer.s3.boto3.client")


class TestS3ClientInit:
    def test_passes_credentials(self, mock_boto3_client):
        S3Client("http://localhost:9000", "key", "secret", "us-east-1")

        mock_boto3_client.assert_called_once()
        kwargs = mock_boto3_client.call_args.kwargs
        assert kwargs["endpoint_url"] == "http://localhost:9000"
        assert kwargs["aws_access_key_id"] == "key"
        assert kwargs["aws_secret_access_key"] == "secret"
        assert kwargs["region_name"] == "us-east-1"

    def test_omits_empty_credentials(self, mock_boto3_client):
        S3Client("", "", "", "us-east-1")

        kwargs = mock_boto3_client.call_args.kwargs
        assert "endpoint_url" not in kwargs
        assert "aws_access_key_id" not in kwargs
        assert "aws_secret_access_key" not in kwargs


class TestGetS3Client:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_s3_client.cache_clear()
        yield
        get_s3_client.cache_clear()

    def test_requires_credentials_together(self, settings, mocker):
        settings.S3_ACCESS_KEY_ID = "key"
        settings.S3_SECRET_ACCESS_KEY = ""
        mocker.patch("mediaviewer.s3.S3Client")

        with pytest.raises(ValueError, match="must be set together"):
            get_s3_client()

    def test_accepts_both_credentials(self, settings, mocker):
        settings.S3_ACCESS_KEY_ID = "key"
        settings.S3_SECRET_ACCESS_KEY = "secret"
        mock_client_cls = mocker.patch("mediaviewer.s3.S3Client")

        get_s3_client()

        mock_client_cls.assert_called_once()


class TestS3ClientMethods:
    @pytest.fixture(autouse=True)
    def setUp(self, mock_boto3_client):
        self.mock_client = mock_boto3_client.return_value
        self.s3 = S3Client("", "", "", "us-east-1")

    def test_upload_file_sets_content_type(self):
        self.s3.upload_file("/tmp/foo.mp4", "bucket", "key/foo.mp4")

        self.mock_client.upload_file.assert_called_once_with(
            "/tmp/foo.mp4",
            "bucket",
            "key/foo.mp4",
            ExtraArgs={"ContentType": "video/mp4"},
        )

    def test_upload_file_with_extra_args(self):
        self.s3.upload_file(
            "/tmp/foo.mp4",
            "bucket",
            "key/foo.mp4",
            extra_args={"ContentType": "video/mp4"},
        )

        self.mock_client.upload_file.assert_called_once_with(
            "/tmp/foo.mp4",
            "bucket",
            "key/foo.mp4",
            ExtraArgs={"ContentType": "video/mp4"},
        )

    def test_upload_file_unknown_extension(self):
        self.s3.upload_file("/tmp/foo", "bucket", "key/foo")

        self.mock_client.upload_file.assert_called_once_with(
            "/tmp/foo",
            "bucket",
            "key/foo",
            ExtraArgs={"ContentType": "application/octet-stream"},
        )

    def test_generate_presigned_url(self, settings):
        settings.S3_PRESIGNED_URL_EXPIRY = 1234

        url = self.s3.generate_presigned_url("bucket", "key/foo.mp4")

        assert url == self.mock_client.generate_presigned_url.return_value
        self.mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "bucket", "Key": "key/foo.mp4"},
            ExpiresIn=1234,
        )

    def test_generate_presigned_url_with_custom_expiry(self):
        self.s3.generate_presigned_url("bucket", "key/foo.mp4", expires_in=60)

        self.mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "bucket", "Key": "key/foo.mp4"},
            ExpiresIn=60,
        )
