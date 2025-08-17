import pytest
from django.core.management import call_command

from mediaviewer.models import VideoProgress


@pytest.mark.parametrize("use_tv", (True, False))
@pytest.mark.django_db
class TestExpireTokens:
    @pytest.fixture(autouse=True)
    def setUp(
        self,
        create_user,
        create_tv_media_file,
        create_movie,
    ):
        self.user = create_user()
        self.command_name = "expirevideoprogress"

        self.mf = create_tv_media_file()
        self.movie = create_movie()

    def test_expire(self, use_tv, settings):
        settings.VIDEO_PROGRESS_HOLDING_PERIOD = 0

        if use_tv:
            self.file = self.mf
            self.movie = None
        else:
            self.file = self.movie
            self.mf = None

        vp = VideoProgress.objects.create(
            user=self.user,
            filename=self.file.full_name,
            hashed_filename=str(id(self.file)),
            media_file=self.mf,
            movie=self.movie,
            offset=100,
        )

        call_command(self.command_name)

        with pytest.raises(VideoProgress.DoesNotExist):
            vp.refresh_from_db()
