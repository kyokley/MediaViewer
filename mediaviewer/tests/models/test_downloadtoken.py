import pytest

from datetime import timedelta
from mediaviewer.models.downloadtoken import DownloadToken
from django.conf import settings


@pytest.mark.django_db
@pytest.mark.parametrize(
    'use_movie', (True, False))
class TestIsValid:
    @pytest.fixture(autouse=True)
    def setUp(self,
              create_tv_media_file,
              create_movie_media_file,
              create_user):
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
        dt.date_created = dt.date_created - timedelta(hours=settings.TOKEN_VALIDITY_LENGTH, seconds=1)
        assert not dt.isvalid
