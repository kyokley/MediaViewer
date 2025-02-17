import logging

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Coalesce

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
            "--force",
            action="store_true",
            help="Clear existing imdb and tmdb fields before populating objects",
        )

    def handle(self, *args, **kwargs):
        limit = kwargs["limit"]
        limit = int(limit) if limit else DEFAULT_LIMIT

        force = kwargs["force"]

        poster_qs = (
            Poster.objects.filter(Q(image="") | Q(release_date__isnull=True))
            .annotate(
                obj_created=Coalesce(
                    "movie__date_created",
                    "tv__date_created",
                    "media_file__date_created",
                )
            )
            .order_by("-obj_created")
        )

        total = poster_qs.count()
        count = 0
        poster_qs = poster_qs[:limit]
        for poster in poster_qs:
            count += 1

            if not poster.ref_obj:
                logger.warning(f"Poster id={poster.id} is orphaned. Removing...")
                poster.delete()

                self.stdout.write(f" {count}/{total}")
                continue
            else:
                if force:
                    poster.imdb = ""
                    poster.tmdb = ""

                try:
                    poster.populate_data()
                    poster.save()
                except Exception as e:
                    logger.warning(f"Got error processing {poster}")
                    logger.warning(e)
                    continue

            self.stdout.write(f" {count}/{total} - {str(poster.ref_obj):<100}")
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS("Done"))
