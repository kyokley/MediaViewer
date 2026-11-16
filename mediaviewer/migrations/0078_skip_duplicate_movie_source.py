import hashlib

from django.db import migrations, transaction


STALE_PATH_ID = 560
STALE_MOVIE_ID = 165
STALE_PATH_SHA256 = "be3d94b6ad42790769489d8e2a04f45bfb3fbf7524669169a1e1f4ac4b8cf0e4"
CANONICAL_PATH_ID = 723
CANONICAL_MOVIE_ID = 328
CANONICAL_PATH_SHA256 = (
    "1aa6de46e7c8f3c2c3f87b72a14f5f17725d4184cf631c8302e8184fe479ae7a"
)


def _path_matches(path, expected_hash):
    return hashlib.sha256((path or "").encode("utf-8")).hexdigest() == expected_hash


def _has_associated_records(MediaFile, MediaPath, media_path_id, alias):
    return (
        MediaFile.objects.using(alias).filter(media_path_id=media_path_id).exists()
        or MediaPath.objects.using(alias)
        .filter(migration_source_id=media_path_id)
        .exists()
    )


def skip_duplicate_movie_source(apps, schema_editor):
    alias = schema_editor.connection.alias
    MediaFile = apps.get_model("mediaviewer", "MediaFile")
    MediaPath = apps.get_model("mediaviewer", "MediaPath")
    Movie = apps.get_model("mediaviewer", "Movie")
    Poster = apps.get_model("mediaviewer", "Poster")

    with transaction.atomic(using=alias):
        stale = (
            MediaPath.objects.using(alias)
            .select_for_update()
            .filter(pk=STALE_PATH_ID)
            .first()
        )
        if stale is None or stale.skip or (stale._path or "").startswith("b2://"):
            return

        if (
            stale.movie_id != STALE_MOVIE_ID
            or stale.tv_id is not None
            or stale.filename not in (None, "")
            or stale.migration_source_id is not None
            or not _path_matches(stale._path, STALE_PATH_SHA256)
            or _has_associated_records(MediaFile, MediaPath, STALE_PATH_ID, alias)
        ):
            raise RuntimeError(
                "Confirmed stale movie source changed "
                f"(MediaPath {STALE_PATH_ID}, Movie {STALE_MOVIE_ID}); refusing exclusion."
            )

        canonical_paths = list(
            MediaPath.objects.using(alias)
            .select_for_update()
            .filter(movie_id=CANONICAL_MOVIE_ID)
            .order_by("pk")
        )
        canonical = canonical_paths[-1] if canonical_paths else None
        canonical_is_b2 = bool(
            canonical and (canonical._path or "").startswith("b2://")
        )
        if (
            canonical is None
            or canonical.pk != CANONICAL_PATH_ID
            or canonical.movie_id != CANONICAL_MOVIE_ID
            or canonical.tv_id is not None
            or canonical.skip
            or canonical.migration_source_id is not None
            or (not canonical_is_b2 and canonical.filename not in (None, ""))
            or not (
                canonical_is_b2 or _path_matches(canonical._path, CANONICAL_PATH_SHA256)
            )
            or _has_associated_records(MediaFile, MediaPath, CANONICAL_PATH_ID, alias)
        ):
            raise RuntimeError(
                "Confirmed canonical movie source changed "
                f"(MediaPath {CANONICAL_PATH_ID}, Movie {CANONICAL_MOVIE_ID}); "
                "refusing stale-source exclusion."
            )

        movies = {
            movie.pk: movie
            for movie in Movie.objects.using(alias)
            .select_for_update()
            .filter(pk__in=(STALE_MOVIE_ID, CANONICAL_MOVIE_ID))
            .order_by("pk")
        }
        if len(movies) != 2:
            raise RuntimeError(
                "Confirmed duplicate movie records changed "
                f"(Movies {STALE_MOVIE_ID} and {CANONICAL_MOVIE_ID}); "
                "refusing stale-source exclusion."
            )
        if movies[STALE_MOVIE_ID].name != movies[CANONICAL_MOVIE_ID].name:
            raise RuntimeError(
                "Confirmed duplicate movie names changed "
                f"(Movies {STALE_MOVIE_ID} and {CANONICAL_MOVIE_ID}); "
                "refusing stale-source exclusion."
            )

        poster_ids = {movies[movie_id]._poster_id for movie_id in movies}
        if None in poster_ids:
            raise RuntimeError(
                "Confirmed duplicate movie poster metadata is missing "
                f"(Movies {STALE_MOVIE_ID} and {CANONICAL_MOVIE_ID}); "
                "refusing stale-source exclusion."
            )
        posters = {
            poster.pk: poster
            for poster in Poster.objects.using(alias)
            .select_for_update()
            .filter(pk__in=poster_ids)
            .order_by("pk")
        }
        stale_poster = posters.get(movies[STALE_MOVIE_ID]._poster_id)
        canonical_poster = posters.get(movies[CANONICAL_MOVIE_ID]._poster_id)
        if (
            stale_poster is None
            or canonical_poster is None
            or not stale_poster.tmdb
            or stale_poster.tmdb != canonical_poster.tmdb
            or stale_poster.release_date is None
            or stale_poster.release_date != canonical_poster.release_date
        ):
            raise RuntimeError(
                "Confirmed duplicate movie metadata changed "
                f"(Movies {STALE_MOVIE_ID} and {CANONICAL_MOVIE_ID}); "
                "refusing stale-source exclusion."
            )

        MediaPath.objects.using(alias).filter(pk=STALE_PATH_ID).update(skip=True)


class Migration(migrations.Migration):
    dependencies = [("mediaviewer", "0077_repair_local_mediafile_filenames")]

    operations = [migrations.RunPython(skip_duplicate_movie_source)]
