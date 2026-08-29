import pytest

from mediaviewer.models import MediaFile


@pytest.mark.django_db
class TestDownloadLinkB2:
    def test_tv_media_file_uses_presigned_url(self, create_tv_media_file, mocker):
        mf = create_tv_media_file()
        mp = mf.media_path
        mp._path = "b2://mybucket/tv/ShowName/"
        mp.save()
        mock_client = mocker.patch("mediaviewer.b2.get_b2_client")
        mock_client.return_value.generate_presigned_url.return_value = (
            "https://presigned/url"
        )

        url = mf.downloadLink("guid")

        assert url == "https://presigned/url"
        mock_client.return_value.generate_presigned_url.assert_called_once_with(
            bucket="mybucket", key=f"tv/ShowName/{mf.filename}", expires_in=None
        )

    def test_movie_uses_stored_filename(self, create_movie, mocker):
        movie = create_movie()
        mp = movie.media_path
        mp._path = "b2://mybucket/movies/Movie Name/"
        mp.filename = "The.Movie.2024.mkv"
        mp.save()
        mock_client = mocker.patch("mediaviewer.b2.get_b2_client")
        mock_client.return_value.generate_presigned_url.return_value = (
            "https://presigned/url"
        )

        url = movie.downloadLink("guid")

        assert url == "https://presigned/url"
        mock_client.return_value.generate_presigned_url.assert_called_once_with(
            bucket="mybucket",
            key="movies/Movie Name/The.Movie.2024.mkv",
            expires_in=None,
        )

    def test_movie_without_filename_raises(self, create_movie, mocker):
        movie = create_movie()
        mp = movie.media_path
        mp._path = "b2://mybucket/movies/Movie Name/"
        mp.save()
        mocker.patch("mediaviewer.b2.get_b2_client")

        with pytest.raises(ValueError, match="no MediaPath.filename"):
            movie.downloadLink("guid")

    def test_local_media_still_uses_waiter(self, create_tv_media_file):
        mf = create_tv_media_file()

        url = mf.downloadLink("guid")

        assert "waiter" in url

    def test_local_movie_still_uses_waiter(self, create_movie):
        movie = create_movie()

        url = movie.downloadLink("guid")

        assert "waiter" in url


@pytest.mark.django_db
class TestAutoPlayDownloadLinkB2:
    def test_b2_returns_presigned_url_without_suffix(
        self, create_tv_media_file, mocker
    ):
        mf = create_tv_media_file()
        mp = mf.media_path
        mp._path = "b2://mybucket/tv/ShowName/"
        mp.save()
        mock_client = mocker.patch("mediaviewer.b2.get_b2_client")
        mock_client.return_value.generate_presigned_url.return_value = (
            "https://presigned/url"
        )

        url = mf.autoplayDownloadLink("guid")

        assert url == "https://presigned/url"

    def test_local_keeps_autoplay_suffix(self, create_tv_media_file):
        mf = create_tv_media_file()

        url = mf.autoplayDownloadLink("guid")

        assert url.endswith("autoplay")

    def test_movie_returns_none(self, create_movie):
        movie = create_movie()

        assert movie.autoplayDownloadLink("guid") is None


@pytest.mark.django_db
class TestMediaFileB2:
    def test_media_file_is_b2(self, create_tv_media_file):
        mf = create_tv_media_file()
        mf.media_path._path = "b2://mybucket/tv/ShowName/"
        mf.media_path.save()

        assert mf.media_path.is_b2
        assert isinstance(mf, MediaFile)
