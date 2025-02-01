import logging

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

logger = logging.getLogger(__file__)
WERT66 = "wert66"


class Command(BaseCommand):
    help = "Clear all passwords"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            logger.info(f"Setting {user}")
            user.set_password(WERT66)
            user.save()

        site = Site.objects.get()
        site.name = "localhost:8000"
        site.domain = "localhost:8000"
        site.save()
