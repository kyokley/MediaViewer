from django.conf import settings as conf_settings

from mediaviewer.management.commands.expiretokens import ExpireCommand
from mediaviewer.models import VideoProgress


class Command(ExpireCommand):
    def handle(self, *args, **kwargs):
        self._handle(
            conf_settings.VIDEO_PROGRESS_HOLDING_PERIOD, VideoProgress, *args, **kwargs
        )
