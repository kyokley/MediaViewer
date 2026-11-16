import hashlib

from django.db import migrations, transaction


SOURCE_PATH_ID = 432
EXPECTED_MOVIE_ID = 37
SOURCE_PATH_SHA256 = "7e7b16fc2f287609031f2660445214d41d30c4f1bff5bf616d762fb6605eb923"


def _matches_source_fingerprint(path):
    return hashlib.sha256((path or "").encode("utf-8")).hexdigest() == (
        SOURCE_PATH_SHA256
    )


def skip_unavailable_movie_source(apps, schema_editor):
    alias = schema_editor.connection.alias
    MediaFile = apps.get_model("mediaviewer", "MediaFile")
    MediaPath = apps.get_model("mediaviewer", "MediaPath")
    Movie = apps.get_model("mediaviewer", "Movie")

    with transaction.atomic(using=alias):
        source = (
            MediaPath.objects.using(alias)
            .select_for_update()
            .filter(pk=SOURCE_PATH_ID)
            .first()
        )
        if source is None or source.skip or (source._path or "").startswith("b2://"):
            return

        if (
            source.movie_id != EXPECTED_MOVIE_ID
            or source.tv_id is not None
            or source.filename not in (None, "")
            or source.migration_source_id is not None
            or not _matches_source_fingerprint(source._path)
        ):
            raise RuntimeError(
                "Confirmed unavailable movie source changed "
                f"(MediaPath {SOURCE_PATH_ID}, Movie {EXPECTED_MOVIE_ID}); "
                "refusing exclusion."
            )

        movie = (
            Movie.objects.using(alias)
            .select_for_update()
            .filter(pk=EXPECTED_MOVIE_ID)
            .first()
        )
        if movie is None:
            raise RuntimeError(
                "Confirmed unavailable movie owner is missing "
                f"(MediaPath {SOURCE_PATH_ID}, Movie {EXPECTED_MOVIE_ID}); "
                "refusing exclusion."
            )

        has_media_files = (
            MediaFile.objects.using(alias).filter(media_path_id=SOURCE_PATH_ID).exists()
        )
        has_migration_targets = (
            MediaPath.objects.using(alias)
            .filter(migration_source_id=SOURCE_PATH_ID)
            .exists()
        )
        sibling_paths = list(
            MediaPath.objects.using(alias)
            .select_for_update()
            .filter(movie_id=EXPECTED_MOVIE_ID)
            .exclude(pk=SOURCE_PATH_ID)
        )
        if has_media_files or has_migration_targets or sibling_paths:
            raise RuntimeError(
                "Confirmed unavailable movie source has unexpected associated paths "
                f"(MediaPath {SOURCE_PATH_ID}, Movie {EXPECTED_MOVIE_ID}); "
                "refusing exclusion."
            )

        MediaPath.objects.using(alias).filter(pk=SOURCE_PATH_ID).update(skip=True)


class Migration(migrations.Migration):
    dependencies = [("mediaviewer", "0078_skip_duplicate_movie_source")]

    operations = [migrations.RunPython(skip_unavailable_movie_source)]
