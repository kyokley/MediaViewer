import argparse

from django.core.management.base import BaseCommand
from django.db import transaction

from mediaviewer.models import WaiterStatus


class Command(BaseCommand):
    help = "Remove obsolete waiter statuses"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction)

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get("dry_run", False) or False

        with transaction.atomic():
            top_ten = WaiterStatus.objects.order_by("-pk")[:10]
            qs = WaiterStatus.objects.exclude(pk__in=top_ten)

            statuses_deleted, _ = qs.delete()

            self.stdout.write(f"Removed {statuses_deleted} WaiterStatus records.")

            if dry_run:
                self.stdout.write(self.style.WARNING("dry-run=True ROLLBACK"))
                transaction.set_rollback(True)
