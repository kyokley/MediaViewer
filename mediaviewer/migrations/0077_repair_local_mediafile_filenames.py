from collections import defaultdict

from django.db import migrations, transaction


TARGETS = (
    (52, (4278, 4472)),
    (55, (1468, 1476, 1483, 1493, 1561, 1568, 1586)),
    (112, (2735, 2737, 2738, 2750, 2752, 2759, 2765, 2766)),
    (
        115,
        (
            2798,
            2799,
            2800,
            2801,
            2802,
            2804,
            2805,
            2808,
            2809,
            2810,
            2812,
            2813,
            2814,
            2816,
            2817,
            2818,
            2819,
            2820,
            2821,
            2823,
            2824,
            2825,
            2826,
            2827,
            2828,
        ),
    ),
    (116, (4288,)),
    (181, (6959,)),
)


def repair_filenames(apps, schema_editor):
    alias = schema_editor.connection.alias
    MediaFile = apps.get_model("mediaviewer", "MediaFile")
    MediaPath = apps.get_model("mediaviewer", "MediaPath")
    path_by_target = {
        media_file_id: path_id
        for path_id, media_file_ids in TARGETS
        for media_file_id in media_file_ids
    }

    with transaction.atomic(using=alias):
        files = list(
            MediaFile.objects.using(alias)
            .select_for_update()
            .filter(pk__in=path_by_target)
            .order_by("pk")
        )
        paths = {
            media_path.pk: media_path
            for media_path in MediaPath.objects.using(alias)
            .select_for_update()
            .filter(pk__in={*path_by_target.values()})
            .order_by("pk")
        }

        planned = []
        for media_file in files:
            if "'" not in media_file.filename:
                continue

            expected_path_id = path_by_target[media_file.pk]
            media_path = paths.get(expected_path_id)
            valid_local_tv_source = (
                media_path is not None
                and media_file.media_path_id == expected_path_id
                and media_path.tv_id is not None
                and media_path.movie_id is None
                and media_file.b2_uuid is None
                and bool(media_path._path)
                and not (media_path._path or "").startswith("b2://")
            )
            if not valid_local_tv_source:
                raise RuntimeError(
                    "Confirmed filename target is no longer a local TV source "
                    f"(MediaFile {media_file.pk}, MediaPath {expected_path_id}); "
                    "refusing filename repair."
                )

            repaired_filename = media_file.filename.replace("'", "")
            if not repaired_filename:
                raise RuntimeError(
                    "Filename repair would produce an empty name "
                    f"(MediaFile {media_file.pk}, MediaPath {expected_path_id}); "
                    "refusing filename repair."
                )
            planned.append((media_file.pk, expected_path_id, repaired_filename))

        planned_by_destination = defaultdict(list)
        for media_file_id, path_id, filename in planned:
            planned_by_destination[(path_id, filename)].append(media_file_id)

        for (path_id, filename), media_file_ids in planned_by_destination.items():
            if len(media_file_ids) > 1:
                raise RuntimeError(
                    "Confirmed filename repair collision between target records "
                    f"(MediaPath {path_id}, MediaFiles {sorted(media_file_ids)}); "
                    "refusing filename repair."
                )

        for media_file_id, path_id, filename in planned:
            collision_id = (
                MediaFile.objects.using(alias)
                .filter(media_path_id=path_id, filename=filename)
                .exclude(pk=media_file_id)
                .values_list("pk", flat=True)
                .first()
            )
            if collision_id is not None:
                raise RuntimeError(
                    "Confirmed filename repair collision with an existing record "
                    f"(MediaPath {path_id}, MediaFiles {media_file_id} and "
                    f"{collision_id}); refusing filename repair."
                )

        for media_file_id, _, filename in planned:
            MediaFile.objects.using(alias).filter(pk=media_file_id).update(
                filename=filename
            )


class Migration(migrations.Migration):
    dependencies = [("mediaviewer", "0076_remove_duplicate_local_mediafiles")]

    operations = [migrations.RunPython(repair_filenames)]
