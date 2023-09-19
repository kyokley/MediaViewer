import logging
from itertools import chain
from django.core.management.base import BaseCommand

from django.db.models import F
from mediaviewer.models import TV, Movie, MediaFile, Poster

DEFAULT_LIMIT = 10
logger = logging.getLogger(__file__)

class Command(BaseCommand):
    help = "Populate missing Poster objects"

    def add_arguments(self, parser):
        parser.add_argument(
            "limit",
            metavar="LIMIT",
            help="Only attempt to populate LIMIT number of Poster objects",
        )

    def handle(self, *args, **kwargs):
        limit = kwargs['limit']
        limit = int(limit) if limit else DEFAULT_LIMIT

        missing_tv = TV.objects.filter(poster=None)
        missing_movie = Movie.objects.filter(poster=None)
        missing_episode = MediaFile.objects.filter(poster=None)

        count = 0
        for media in chain(missing_tv, missing_movie, missing_episode):
            Poster.objects.create_from_ref_obj(media)
            count += 1

            if count > limit:
                break
