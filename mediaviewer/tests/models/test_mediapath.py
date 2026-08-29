import pytest


@pytest.mark.django_db
class TestMediaPathB2:
    def test_is_b2_false_for_local_path(self, create_media_path, create_tv):
        mp = create_media_path(tv=create_tv())

        assert not mp.is_b2

    def test_is_b2_true_for_b2_uri(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/ShowName/", tv=create_tv())

        assert mp.is_b2

    def test_bucket_and_key(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/ShowName/", tv=create_tv())

        assert mp.bucket == "mybucket"
        assert mp.key == "tv/ShowName/"

    def test_bucket_and_key_are_none_for_local(self, create_media_path, create_tv):
        mp = create_media_path(tv=create_tv())

        assert mp.bucket is None
        assert mp.key is None

    def test_path_returns_uri_string_for_b2(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/ShowName/", tv=create_tv())

        assert mp.path == "b2://mybucket/tv/ShowName/"

    def test_file_key(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/ShowName/", tv=create_tv())

        assert mp.file_key("S01E01.mp4") == "tv/ShowName/S01E01.mp4"

    def test_presigned_url(self, create_media_path, create_tv, mocker):
        mp = create_media_path(path="b2://mybucket/tv/ShowName/", tv=create_tv())
        mock_client = mocker.patch("mediaviewer.b2.get_b2_client")
        mock_client.return_value.generate_presigned_url.return_value = (
            "https://presigned/url"
        )

        url = mp.presigned_url("S01E01.mp4")

        assert url == "https://presigned/url"
        mock_client.return_value.generate_presigned_url.assert_called_once_with(
            bucket="mybucket", key="tv/ShowName/S01E01.mp4", expires_in=None
        )

    def test_presigned_url_with_custom_expiry(
        self, create_media_path, create_tv, mocker
    ):
        mp = create_media_path(path="b2://mybucket/tv/ShowName/", tv=create_tv())
        mock_client = mocker.patch("mediaviewer.b2.get_b2_client")

        mp.presigned_url("S01E01.mp4", expires_in=60)

        mock_client.return_value.generate_presigned_url.assert_called_once_with(
            bucket="mybucket", key="tv/ShowName/S01E01.mp4", expires_in=60
        )


@pytest.mark.django_db
class TestMediaPathB2EdgeCases:
    def test_bucket_with_dots(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://my.bucket.name/tv/ShowName/", tv=create_tv())

        assert mp.bucket == "my.bucket.name"
        assert mp.key == "tv/ShowName/"

    def test_key_with_question_mark(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/Show?Name/", tv=create_tv())

        assert mp.bucket == "mybucket"
        assert mp.key == "tv/Show?Name/"

    def test_key_with_hash(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/Show#Name/", tv=create_tv())

        assert mp.bucket == "mybucket"
        assert mp.key == "tv/Show#Name/"

    def test_empty_prefix(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/", tv=create_tv())

        assert mp.bucket == "mybucket"
        assert mp.key == ""

    def test_missing_trailing_slash(self, create_media_path, create_tv):
        mp = create_media_path(path="b2://mybucket/tv/ShowName", tv=create_tv())

        assert mp.file_key("S01E01.mp4") == "tv/ShowName/S01E01.mp4"

    def test_uppercase_scheme_not_b2(self, create_media_path, create_tv):
        mp = create_media_path(path="B2://mybucket/tv/ShowName/", tv=create_tv())

        assert not mp.is_b2
        assert mp.bucket is None
        assert mp.key is None
