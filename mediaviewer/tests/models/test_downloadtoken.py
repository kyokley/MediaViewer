from datetime import timedelta

import pytest
from django.conf import settings

from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.django_db
@pytest.mark.parametrize("use_movie", (True, False))
class TestIsValid:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv_media_file, create_movie_media_file, create_user):
        self.user = create_user()

        self.tv_mf = create_tv_media_file()
        self.movie_mf = create_movie_media_file()

    def test_is_valid(self, use_movie):
        if use_movie:
            mf = self.movie_mf
        else:
            mf = self.tv_mf

        dt = DownloadToken.objects.from_media_file(self.user, mf)
        assert dt.isvalid

    def test_is_invalid(self, use_movie):
        if use_movie:
            mf = self.movie_mf
        else:
            mf = self.tv_mf

        dt = DownloadToken.objects.from_media_file(self.user, mf)
        dt.date_created = dt.date_created - timedelta(
            hours=settings.TOKEN_VALIDITY_LENGTH, seconds=1
        )
        assert not dt.isvalid


@pytest.mark.django_db
class TestIsMCP:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv_media_file, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.user = create_user()
        self.mf = create_tv_media_file()

    def test_is_mcp_defaults_to_false(self):
        """DownloadToken.is_mcp defaults to False."""
        dt = DownloadToken.objects.from_media_file(self.user, self.mf)
        assert not dt.is_mcp

    def test_is_mcp_true_skips_message_creation(self, mocker):
        """When is_mcp=True, no Message is created."""
        mock_message = mocker.patch(
            "mediaviewer.models.downloadtoken.Message.createLastWatchedMessage"
        )
        dt = DownloadToken.objects.from_media_file(self.user, self.mf, is_mcp=True)
        assert dt.is_mcp
        mock_message.assert_not_called()

    def test_is_mcp_false_creates_message(self, mocker):
        """When is_mcp=False, a Message is created (existing behavior)."""
        mock_message = mocker.patch(
            "mediaviewer.models.downloadtoken.Message.createLastWatchedMessage"
        )
        dt = DownloadToken.objects.from_media_file(self.user, self.mf, is_mcp=False)
        assert not dt.is_mcp
        mock_message.assert_called_once()

    def test_is_mcp_true_from_movie(self, create_movie_media_file, mocker):
        """from_movie with is_mcp=True skips message creation."""
        movie_mf = create_movie_media_file()
        mock_message = mocker.patch(
            "mediaviewer.models.downloadtoken.Message.createLastWatchedMessage"
        )
        dt = DownloadToken.objects.from_movie(self.user, movie_mf.movie, is_mcp=True)
        assert dt.is_mcp
        mock_message.assert_not_called()
