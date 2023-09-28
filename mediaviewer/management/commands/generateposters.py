import logging
from django.core.management.base import BaseCommand

from mediaviewer.models import Poster

DEFAULT_LIMIT = 10
logger = logging.getLogger(__file__)

class Command(BaseCommand):
    help = "Populate missing Poster objects"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            metavar="LIMIT",
            help="Only attempt to populate LIMIT number of Poster objects",
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Clear existing imdb and tmdb fields before populating objects',
        )

    def handle(self, *args, **kwargs):
        limit = kwargs['limit']
        limit = int(limit) if limit else DEFAULT_LIMIT

        force = kwargs['force']

        poster_qs = Poster.objects.filter(image='').order_by('id')

        total = poster_qs.count()
        count = 0
        for poster in poster_qs:
            count += 1

            if count > limit:
                break

            if force:
                poster.imdb = ''
                poster.tmdb = ''

            poster._populate_data()
            poster.save()

            print(f'{count}/{total}', end='\r')
        print()