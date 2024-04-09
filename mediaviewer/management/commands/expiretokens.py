import argparse

from datetime import timedelta

from django.core.management.base import BaseCommand
from mediaviewer.models.downloadtoken import DownloadToken

from django.conf import settings as conf_settings
from django.utils import timezone
from django.db import transaction


class Command(BaseCommand):
    help = 'Remove expired tokens'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run',
                            action=argparse.BooleanOptionalAction)

    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']

        expiry_time = (
            timezone.now() - timedelta(hours=conf_settings.TOKEN_HOLDING_PERIOD)
        )

        with transaction.atomic():
            # Remove old tokens
            tokens_deleted, _ = (
                DownloadToken.objects.filter(date_created__lt=expiry_time).delete()
            )

            self.stdout.write(f'Removed {tokens_deleted} tokens.')

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        'dry-run=True ROLLBACK'
                    )
                )
                transaction.set_rollback(True)
