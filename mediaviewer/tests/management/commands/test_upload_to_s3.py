import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
class TestUploadToS3:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_client = mocker.patch("mediaviewer.s3.get_s3_client").return_value

    def test_requires_bucket(self, monkeypatch):
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

        with pytest.raises(CommandError):
            call_command("upload_to_s3")

    def test_upload_tv_media_path(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        dir_name = mp.path.name
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket", "--prefix", "tv/")

        mp.refresh_from_db()
        assert mp._path == f"s3://mybucket/tv/{mp.pk}/{dir_name}/"
        assert mp.is_s3
        assert mp.filename is None
        self.mock_client.upload_file.assert_called_once_with(
            local_file, "mybucket", f"tv/{mp.pk}/{dir_name}/S01E01.mp4"
        )

    def test_upload_movie_media_path(self, create_movie):
        movie = create_movie()
        mp = movie.media_path
        dir_name = mp.path.name
        video_file = mp.path / "The.Movie.2024.mkv"
        video_file.parent.mkdir(parents=True, exist_ok=True)
        video_file.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket")

        mp.refresh_from_db()
        assert mp._path == f"s3://mybucket/{mp.pk}/{dir_name}/"
        assert mp.filename == "The.Movie.2024.mkv"
        self.mock_client.upload_file.assert_called_once_with(
            video_file, "mybucket", f"{mp.pk}/{dir_name}/The.Movie.2024.mkv"
        )

    def test_prefix_normalization(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        dir_name = mp.path.name
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket", "--prefix", "tv")

        mp.refresh_from_db()
        assert mp._path == f"s3://mybucket/tv/{mp.pk}/{dir_name}/"

    def test_same_basename_media_paths_do_not_collide(
        self, create_tv_media_file, tmp_path
    ):
        mf1 = create_tv_media_file(filename="S01E01.mp4")
        mp1 = mf1.media_path
        dir_name1 = mp1.path.name
        local_file = mp1.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")

        mf2 = create_tv_media_file(filename="S01E01.mp4")
        mp2 = mf2.media_path
        mp2._path = str(tmp_path / "other" / dir_name1)
        mp2.save()
        local_file2 = mp2.path / "S01E01.mp4"
        local_file2.parent.mkdir(parents=True, exist_ok=True)
        local_file2.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket")

        mp1.refresh_from_db()
        mp2.refresh_from_db()
        assert mp1._path != mp2._path
        assert mp1._path == f"s3://mybucket/{mp1.pk}/{dir_name1}/"
        assert mp2._path == f"s3://mybucket/{mp2.pk}/{dir_name1}/"

    def test_skips_missing_files(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        original_path = mp._path

        call_command("upload_to_s3", "--bucket", "mybucket")

        mp.refresh_from_db()
        assert mp._path == original_path
        assert not mp.is_s3
        self.mock_client.upload_file.assert_not_called()

    def test_skips_s3_media_paths(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        mp._path = "s3://mybucket/tv/ShowName/"
        mp.save()

        call_command("upload_to_s3", "--bucket", "mybucket")

        self.mock_client.upload_file.assert_not_called()

    def test_skips_media_paths_with_skip_flag(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        mp.skip = True
        mp.save()
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket")

        self.mock_client.upload_file.assert_not_called()

    def test_skips_hidden_media_files(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        hidden_mf = create_tv_media_file(filename="S01E02.mp4")
        hidden_mf.hide = True
        hidden_mf.save()
        mp = mf.media_path
        dir_name = mp.path.name
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")
        (mp.path / "S01E02.mp4").write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket")

        mp.refresh_from_db()
        assert mp._path == f"s3://mybucket/{mp.pk}/{dir_name}/"
        self.mock_client.upload_file.assert_called_once_with(
            local_file, "mybucket", f"{mp.pk}/{dir_name}/S01E01.mp4"
        )

    def test_upload_failure_does_not_flip_path(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")
        self.mock_client.upload_file.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            call_command("upload_to_s3", "--bucket", "mybucket")

        mp.refresh_from_db()
        assert not mp.is_s3

    def test_delete_local(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket", "--delete-local")

        assert not local_file.exists()

    def test_media_path_option(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        dir_name = mp.path.name
        local_file = mp.path / "S01E01.mp4"
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(b"data")

        call_command("upload_to_s3", "--bucket", "mybucket", "--media-path", str(mp.pk))

        mp.refresh_from_db()
        assert mp._path == f"s3://mybucket/{mp.pk}/{dir_name}/"
        self.mock_client.upload_file.assert_called_once_with(
            local_file, "mybucket", f"{mp.pk}/{dir_name}/S01E01.mp4"
        )

    def test_media_path_option_already_s3(self, create_tv_media_file):
        mf = create_tv_media_file(filename="S01E01.mp4")
        mp = mf.media_path
        mp._path = "s3://mybucket/tv/ShowName/"
        mp.save()

        call_command("upload_to_s3", "--bucket", "mybucket", "--media-path", str(mp.pk))

        self.mock_client.upload_file.assert_not_called()

    def test_movie_without_video_file_is_skipped(self, create_movie):
        movie = create_movie()
        mp = movie.media_path

        call_command("upload_to_s3", "--bucket", "mybucket")

        mp.refresh_from_db()
        assert not mp.is_s3
        self.mock_client.upload_file.assert_not_called()


@pytest.mark.django_db
class TestFindVideoFile:
    def test_finds_video_file(self, tmp_path):
        from mediaviewer.management.commands.upload_to_s3 import Command

        (tmp_path / "poster.jpg").write_bytes(b"data")
        video = tmp_path / "The.Movie.2024.mkv"
        video.write_bytes(b"data")

        assert Command._find_video_file(tmp_path) == video

    def test_prefers_largest_video_file(self, tmp_path):
        from mediaviewer.management.commands.upload_to_s3 import Command

        trailer = tmp_path / "trailer.mp4"
        trailer.write_bytes(b"small")
        main = tmp_path / "The.Movie.2024.mkv"
        main.write_bytes(b"x" * 100)

        assert Command._find_video_file(tmp_path) == main

    def test_returns_none_when_no_video(self, tmp_path):
        from mediaviewer.management.commands.upload_to_s3 import Command

        (tmp_path / "poster.jpg").write_bytes(b"data")

        assert Command._find_video_file(tmp_path) is None

    def test_returns_none_for_missing_directory(self):
        from mediaviewer.management.commands.upload_to_s3 import Command

        assert Command._find_video_file(None) is None
