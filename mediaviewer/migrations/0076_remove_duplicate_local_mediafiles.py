from django.db import migrations, transaction


DUPLICATES = (
    (
        288,
        7999,
        8001,
    ),
    (
        378,
        9955,
        9956,
    ),
)


def remove_confirmed_duplicates(apps, schema_editor):
    alias = schema_editor.connection.alias
    MediaFile = apps.get_model("mediaviewer", "MediaFile")
    MediaPath = apps.get_model("mediaviewer", "MediaPath")
    Poster = apps.get_model("mediaviewer", "Poster")
    TV = apps.get_model("mediaviewer", "TV")
    Movie = apps.get_model("mediaviewer", "Movie")

    with transaction.atomic(using=alias):
        for path_id, loser_id, keeper_id in DUPLICATES:
            files = list(
                MediaFile.objects.using(alias)
                .select_for_update()
                .filter(pk__in=(loser_id, keeper_id))
                .order_by("pk")
            )
            if len(files) != 2:
                continue

            media_path = (
                MediaPath.objects.using(alias)
                .select_for_update()
                .filter(pk=path_id)
                .first()
            )
            by_id = {media_file.pk: media_file for media_file in files}
            filename = by_id[keeper_id].filename
            for media_file_id in (loser_id, keeper_id):
                media_file = by_id[media_file_id]
                local_tv_source = (
                    media_path is not None
                    and media_file.media_path_id == path_id
                    and media_file.filename == filename
                    and media_path.tv_id is not None
                    and media_path.movie_id is None
                    and media_file.b2_uuid is None
                    and bool(media_path._path)
                    and not (media_path._path or "").startswith("b2://")
                )
                if not local_tv_source:
                    raise RuntimeError(
                        "Confirmed duplicate MediaFile records changed since "
                        f"confirmation (MediaFile {media_file_id}, "
                        f"MediaPath {path_id}); refusing deletion."
                    )

            poster_id = by_id[loser_id]._poster_id
            MediaFile.objects.using(alias).filter(pk=loser_id).delete()

            if poster_id is not None:
                still_referenced = (
                    MediaFile.objects.using(alias).filter(_poster_id=poster_id).exists()
                    or TV.objects.using(alias).filter(_poster_id=poster_id).exists()
                    or Movie.objects.using(alias).filter(_poster_id=poster_id).exists()
                )
                if not still_referenced:
                    Poster.objects.using(alias).filter(pk=poster_id).delete()


class Migration(migrations.Migration):
    dependencies = [("mediaviewer", "0075_mediapath_migration_source")]

    operations = [migrations.RunPython(remove_confirmed_duplicates)]
