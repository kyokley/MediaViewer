import pytest
from datetime import timedelta

from django.utils import timezone

from django.core.management import call_command
from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.parametrize(
    'use_tv',
    (True, False))
@pytest.mark.django_db
class TestExpireTokens:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user()
        self.command_name = 'expiretokens'

    def test_valid(self,
                   use_tv,
                   create_tv_media_file,
                   create_movie,
                   ):
        if use_tv:
            mf = create_tv_media_file()
            dt = DownloadToken.objects.from_media_file(
                self.user,
                mf)
        else:
            movie = create_movie()
            dt = DownloadToken.objects.from_movie(
                self.user,
                movie)

        assert dt.isvalid

        call_command(self.command_name)

        dt.refresh_from_db()

    def test_expired(self,
                     use_tv,
                     create_tv_media_file,
                     create_movie,
                     settings,
                     ):
        test_time_period = 1
        settings.TOKEN_VALIDITY_LENGTH = test_time_period
        settings.TOKEN_HOLDING_PERIOD = test_time_period

        if use_tv:
            mf = create_tv_media_file()
            dt = DownloadToken.objects.from_media_file(
                self.user,
                mf)
        else:
            movie = create_movie()
            dt = DownloadToken.objects.from_movie(
                self.user,
                movie)

        dt.date_created = timezone.now() - timedelta(hours=test_time_period)
        dt.save()

        assert not dt.isvalid

        call_command(self.command_name)

        with pytest.raises(DownloadToken.DoesNotExist):
            dt.refresh_from_db()
