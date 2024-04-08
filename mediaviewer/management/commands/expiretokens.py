from datetime import timedelta

from django.core.management.base import BaseCommand
from mediaviewer.models.downloadtoken import DownloadToken

from django.conf import settings as conf_settings
from django.utils import timezone


class Command(BaseCommand):
    help = 'Remove expired tokens'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        expiry_time = (
            timezone.now() - timedelta(hours=conf_settings.TOKEN_HOLDING_PERIOD)
        )

        # Remove old tokens
        DownloadToken.objects.filter(date_created__lt=expiry_time).delete()
