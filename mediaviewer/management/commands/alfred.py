from enum import Enum

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class StrEnum(str, Enum):
    @classmethod
    def from_string(cls, str_type):
        if str_type is not None:
            for enum_type in cls:
                if enum_type.value.lower() == str_type.strip().lower():
                    return enum_type
        return None

    def __str__(self):
        return self.value


class Actions(StrEnum):
    STATUS = "status"


class Command(BaseCommand):
    help = "Management commands for Alfred"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            metavar="ACTION",
            help="Action to take. Currently, STATUS is the only unavailable option",
        )

    def handle(self, *args, **kwargs):
        action = kwargs["action"]

        if Actions.from_string(action) == Actions.STATUS:
            try:
                resp = requests.get(
                    settings.WAITER_STATUS_URL, timeout=settings.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                data = resp.json()

                if "status" not in data or not data["status"]:
                    failureReason = "Bad Symlink"
                else:
                    failureReason = ""

                response = {
                    "status": data.get("status", False),
                    "failureReason": failureReason,
                }
                self.stdout.write(self.style.SUCCESS(str(response)))
            except Exception as e:
                raise CommandError(e)
        else:
            raise CommandError(
                f'Got action "{action}". Valid actions are: {", ".join(Actions)}'
            )
