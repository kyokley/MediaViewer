import argparse

from datetime import timedelta

from django.core.management.base import BaseCommand
from mediaviewer.models import VideoProgress, DownloadToken

from django.conf import settings as conf_settings
from django.utils import timezone
from django.db import transaction


class ExpireCommand(BaseCommand):
    help = "Remove expired tokens"

    FILTER_FIELD = {DownloadToken: "date_created", VideoProgress: "date_edited"}

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction)

    def _handle(self, expiry_length, klass, *args, **kwargs):
        dry_run = kwargs.get("dry_run", False) or False

        expiry_time = timezone.now() - timedelta(hours=expiry_length)

        with transaction.atomic():
            qs = klass.objects.filter(
                **{
                    f"{self.FILTER_FIELD[klass]}__lt": expiry_time,
                }
            )

            # Remove old tokens
            tokens_deleted, _ = qs.delete()

            self.stdout.write(f"Removed {tokens_deleted} {klass.__name__} records.")

            if dry_run:
                self.stdout.write(self.style.WARNING("dry-run=True ROLLBACK"))
                transaction.set_rollback(True)


class Command(ExpireCommand):
    def handle(self, *args, **kwargs):
        self._handle(conf_settings.TOKEN_HOLDING_PERIOD, DownloadToken, *args, **kwargs)
