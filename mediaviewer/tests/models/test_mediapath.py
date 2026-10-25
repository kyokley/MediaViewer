import pytest

from mediaviewer.models import MediaPath


class TestMediaPathB2Layout:
    def test_model_has_no_layout_field_and_uses_nested_prefix(self):
        mp = MediaPath(_path="b2://bucket/archive/Show/", pk=123)

        assert "b2_layout_version" not in {
            field.name for field in MediaPath._meta.get_fields()
        }
        assert mp.b2_upload_prefix == "archive/000/000/123/"

    @pytest.mark.parametrize(
        ("media_path_id", "expected"),
        [
            (1, "000/000/001/"),
            (999, "000/000/999/"),
            (1000, "000/001/000/"),
            (1234567, "001/234/567/"),
            (999999999, "999/999/999/"),
        ],
    )
    def test_b2_upload_prefix(self, media_path_id, expected):
        mp = MediaPath(_path="b2://bucket/archive/Show/", pk=media_path_id)

        assert mp.b2_upload_prefix == f"archive/{expected}"

    @pytest.mark.parametrize(
        "media_path_id", [0, -1, None, "123", 1.5, True, 1000000000]
    )
    def test_b2_upload_prefix_rejects_invalid_ids(self, media_path_id):
        mp = MediaPath(_path="b2://bucket/archive/Show/", pk=media_path_id)

        with pytest.raises(ValueError, match="1 through 999999999"):
            mp.b2_upload_prefix

    def test_prefix_replaces_stored_logical_id_without_duplicate_shards(self):
        mp = MediaPath(_path="b2://bucket/archive/123/Show/", pk=123)

        assert mp.b2_upload_prefix == "archive/000/000/123/"

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("123/Show/", "000/000/123/"),
            ("archive/123/Show/", "archive/000/000/123/"),
            ("/Show/", "/000/000/123/"),
            ("//Show/", "//000/000/123/"),
        ],
    )
    def test_prefix_preserves_root_and_parent_prefix(self, key, expected):
        mp = MediaPath(_path=f"b2://bucket/{key}", pk=123)

        assert mp.b2_upload_prefix == expected


@pytest.mark.django_db
class TestMediaPathB2:
    @pytest.mark.parametrize(
        ("path_template", "expected_template"),
        [
            ("b2://bucket/tv/Show/", "tv/{id}/"),
            ("b2://bucket/archive/nested/Show/", "archive/nested/{id}/"),
            ("b2://bucket/archive/{pk}/Show/", "archive/{id}/"),
            ("b2://bucket/Show/", "{id}/"),
            ("b2://bucket//Show/", "/{id}/"),
        ],
    )
    def test_b2_upload_prefix(
        self, create_media_path, create_tv, path_template, expected_template
    ):
        mp = create_media_path(path=path_template.format(pk="TEMP"), tv=create_tv())
        mp._path = path_template.format(pk=mp.pk)
        mp.save()
        padded_id = f"{mp.pk:09d}"
        nested_id = f"{padded_id[:3]}/{padded_id[3:6]}/{padded_id[6:]}"
        expected = expected_template.format(id=nested_id)
        assert mp.b2_upload_prefix == expected

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
