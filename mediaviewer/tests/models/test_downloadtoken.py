import mock
import pytest

from mediaviewer.tests import helpers
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from django.conf import settings


@pytest.mark.django_db
class TestDownloadToken:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_save = mocker.patch(
            "mediaviewer.models.downloadtoken.DownloadToken.save"
        )

        self.mock_objects = mocker.patch(
            "mediaviewer.models.downloadtoken.DownloadToken.objects"
        )

        self.mock_createLastWatchedMessage = mocker.patch(
            "mediaviewer.models.downloadtoken.Message.createLastWatchedMessage"
        )

        self.user = helpers.create_user()

        self.path = Path.objects.create(
            localpathstr="/path/to/file",
            remotepathstr="/path/to/file",
            is_movie=False,
        )

        self.file = File.new(
            "some file",
            self.path,
        )

    def test_new(self):
        self.mock_objects.count.return_value = (
            settings.MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS + 1
        )
        mock_ordered_query = mock.MagicMock()
        old_token = mock.create_autospec(DownloadToken)
        mock_ordered_query.first.return_value = old_token
        self.mock_objects.order_by.return_value = mock_ordered_query
        dt = DownloadToken.new(self.user, self.file)

        assert dt.filename == "some file"
        assert dt.path == "/path/to/file"
        assert not dt.ismovie
        assert dt.displayname == "some file"
        assert dt.file == self.file
        self.mock_save.assert_called_once_with()
        assert self.mock_objects.count.called
        assert old_token.delete.called
        self.mock_createLastWatchedMessage.assert_called_once_with(self.user, self.file)

    def test_isvalid(self):
        self.mock_objects.count.return_value = 1
        dt = DownloadToken.new(self.user, self.file)
        assert dt.isvalid
