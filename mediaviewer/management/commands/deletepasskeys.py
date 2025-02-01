import logging

import requests
from django.conf import settings as conf_settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

logger = logging.getLogger(__file__)


class Command(BaseCommand):
    help = "Delete bitwarden passkey credentials"

    def add_arguments(self, parser):
        parser.add_argument(
            "user",
            metavar="USER",
            help="User to delete credentials for",
        )

    def handle(self, *args, **kwargs):
        userid = kwargs["user"]
        user = self.get_user(userid)

        if user is None:
            self.stdout.write(
                self.style.WARNING(f"Could not find user for userid={userid}")
            )
            self.stdout.write(
                self.style.WARNING(
                    f"Attempting to query bitwarden database directly with {userid}"
                )
            )
            username = userid
        else:
            username = user.username

        resp = requests.get(
            f"{conf_settings.PASSKEY_API_URL}/credentials/list",
            params={"userId": username},
            headers={
                "ApiSecret": conf_settings.PASSKEY_API_PRIVATE_KEY,
            },
            timeout=conf_settings.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        json_data = resp.json()

        creds = [x["descriptor"]["id"] for x in json_data["values"]]

        for cred in creds:
            payload = {
                "credentialId": cred,
            }

            resp = requests.post(
                f"{conf_settings.PASSKEY_API_URL}/credentials/delete",
                json=payload,
                headers={
                    "ApiSecret": conf_settings.PASSKEY_API_PRIVATE_KEY,
                },
                timeout=conf_settings.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            self.stdout.write(self.style.SUCCESS(f"Deleted {cred}"))

    def get_user(self, userid):
        try:
            user = User.objects.get(pk=userid)
        except Exception as e:
            self.stdout.write("Failed to get user by pk")
            self.stdout.write(self.style.WARNING(e))
            try:
                user = User.objects.get(username=userid)
            except Exception as e:
                self.stdout.write("Failed to get user by username")
                self.stdout.write(self.style.WARNING(e))

                try:
                    user = User.objects.get(email__iexact=userid)
                except Exception as e:
                    self.stdout.write("Failed to get user by email")
                    self.stdout.write(self.style.WARNING(e))
                    self.stdout.write(
                        self.style.ERROR("No remaining methods to attempt")
                    )
                    return None
        return user
