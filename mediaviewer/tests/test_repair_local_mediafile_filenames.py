import importlib
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from mediaviewer.models import (
    Comment,
    DownloadToken,
    MediaFile,
    MediaPath,
    Movie,
    TV,
    VideoProgress,
)


MIGRATION = importlib.import_module(
    "mediaviewer.migrations.0077_repair_local_mediafile_filenames"
)
TARGETS = (
    (52, (4278, 4472)),
    (55, (1468, 1476, 1483, 1493, 1561, 1568, 1586)),
    (
        112,
        (
            2735,
            2737,
            2738,
            2750,
            2752,
            2759,
            2765,
            2766,
        ),
    ),
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
EXPECTED_IDS = {media_file_id for _, ids in TARGETS for media_file_id in ids}


def _run_migration():
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0076_remove_duplicate_local_mediafiles")]
    )
    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.repair_filenames(state.apps, schema_editor)


def _create_targets(*, quoted=True):
    paths = {}
    expected_paths = dict(TARGETS)
    for path_id, ids in TARGETS:
        tv = TV.objects.create(name=f"test show {path_id}")
        paths[path_id] = MediaPath.objects.create(
            pk=path_id, tv=tv, _path=f"/local/test-{path_id}"
        )
        for media_file_id in ids:
            filename = f"sample-{media_file_id}'s-episode.mp4"
            if not quoted:
                filename = filename.replace("'", "")
            MediaFile.objects.create(
                pk=media_file_id,
                media_path=paths[path_id],
                filename=filename,
                display_name=f"episode {media_file_id}",
            )
    return paths, expected_paths


@pytest.mark.django_db(transaction=True)
def test_migration_repairs_exact_44_filenames_without_changing_other_data():
    paths, _ = _create_targets()
    assert MIGRATION.TARGETS == TARGETS
    non_target = MediaFile.objects.create(
        pk=13000,
        media_path=paths[52],
        filename="not-target's-episode.mp4",
        display_name="non-target",
    )
    user = get_user_model().objects.create_user(username="filename-repair-test")
    target_id = 4278
    target = MediaFile.objects.get(pk=target_id)
    comment = Comment.objects.create(user=user, media_file=target, viewed=True)
    progress = VideoProgress.objects.create(
        user=user,
        filename=target.filename,
        hashed_filename="stable-progress-hash",
        offset=12.5,
        media_file=target,
    )
    token = DownloadToken.objects.create(
        user=user,
        path="/local/test-52",
        filename=target.filename,
        displayname="existing token",
        media_file=target,
    )
    before = {
        row.pk: row
        for row in MediaFile.objects.filter(pk__in=EXPECTED_IDS).order_by("pk")
    }
    before_values = {
        media_file_id: MediaFile.objects.filter(pk=media_file_id).values().get()
        for media_file_id in EXPECTED_IDS
    }

    assert len(EXPECTED_IDS) == 44
    assert {row.media_path_id for row in before.values()} == {
        path_id for path_id, _ in TARGETS
    }
    _run_migration()

    for path_id, media_file_ids in TARGETS:
        for media_file_id in media_file_ids:
            row = MediaFile.objects.get(pk=media_file_id)
            original = before_values[media_file_id]
            assert row.filename == original["filename"].replace("'", "")
            updated = MediaFile.objects.filter(pk=media_file_id).values().get()
            assert updated == {**original, "filename": row.filename}
    assert (
        MediaFile.objects.get(pk=non_target.pk).filename == "not-target's-episode.mp4"
    )
    assert Comment.objects.get(pk=comment.pk).viewed is True
    assert (
        VideoProgress.objects.get(pk=progress.pk).hashed_filename
        == "stable-progress-hash"
    )
    assert (
        VideoProgress.objects.get(pk=progress.pk).filename
        == before_values[target_id]["filename"]
    )
    assert (
        DownloadToken.objects.get(pk=token.pk).filename
        == before_values[target_id]["filename"]
    )
    assert DownloadToken.objects.get(pk=token.pk).media_file_id == target_id
    assert MediaPath.objects.filter(pk__in=paths).count() == len(TARGETS)


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_migration_skips_missing_and_already_corrected_targets_and_is_repeatable():
    paths, _ = _create_targets()
    MediaFile.objects.filter(pk=4278).delete()
    already_corrected = MediaFile.objects.get(pk=4472)
    already_corrected.filename = "already-corrected.mp4"
    already_corrected.b2_uuid = uuid.uuid4()
    already_corrected.media_path = MediaPath.objects.create(
        tv=None, _path="b2://test-bucket/already-moved"
    )
    already_corrected.save()

    _run_migration()
    _run_migration()

    assert not MediaFile.objects.filter(pk=4278).exists()
    already_corrected.refresh_from_db()
    assert already_corrected.filename == "already-corrected.mp4"
    assert already_corrected.b2_uuid is not None
    assert already_corrected.media_path_id != paths[52].pk


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@pytest.mark.parametrize(
    "scenario",
    ["wrong-parent", "remote-path", "empty-path", "remote-child", "movie"],
    ids=("wrong-parent", "remote-path", "empty-path", "remote-child", "movie"),
)
def test_migration_rejects_quoted_target_outside_expected_local_tv_source(scenario):
    expected_tv = TV.objects.create(name="expected show")
    if scenario == "remote-path":
        path = MediaPath.objects.create(
            pk=52, tv=expected_tv, _path="b2://test-bucket/remote"
        )
    elif scenario == "empty-path":
        path = MediaPath.objects.create(pk=52, tv=expected_tv, _path="")
    elif scenario == "remote-child":
        path = MediaPath.objects.create(pk=52, tv=expected_tv, _path="/local/child")
    elif scenario == "movie":
        movie = Movie.objects.create(name="other movie")
        path = MediaPath.objects.create(pk=52, _path="/local/movie", movie=movie)
    else:
        MediaPath.objects.create(pk=52, tv=expected_tv, _path="/local/expected")
        other_tv = TV.objects.create(name="other show")
        path = MediaPath.objects.create(_path="/local/other", tv=other_tv)
    row = MediaFile.objects.create(
        pk=4278,
        media_path=path,
        filename="guarded's-episode.mp4",
        display_name="guarded",
        b2_uuid=uuid.uuid4() if scenario == "remote-child" else None,
    )

    with pytest.raises(RuntimeError, match="MediaFile 4278.*MediaPath 52"):
        _run_migration()
    row.refresh_from_db()
    assert row.filename == "guarded's-episode.mp4"


@pytest.mark.django_db(transaction=True)
def test_migration_rejects_empty_normalized_name_without_other_updates():
    first_tv = TV.objects.create(name="first show")
    first_path = MediaPath.objects.create(pk=55, tv=first_tv, _path="/local/first")
    MediaFile.objects.create(
        pk=1468,
        media_path=first_path,
        filename="valid's-episode.mp4",
        display_name="valid target",
    )
    empty_tv = TV.objects.create(name="empty show")
    empty_path = MediaPath.objects.create(pk=52, tv=empty_tv, _path="/local/empty")
    MediaFile.objects.create(
        pk=4278,
        media_path=empty_path,
        filename="'''",
        display_name="empty normalized target",
    )

    with pytest.raises(RuntimeError, match="empty name.*MediaFile 4278"):
        _run_migration()

    assert MediaFile.objects.get(pk=1468).filename == "valid's-episode.mp4"
    assert MediaFile.objects.get(pk=4278).filename == "'''"


@pytest.mark.django_db(transaction=True)
def test_migration_aborts_before_updates_on_existing_destination_collision():
    paths, _ = _create_targets()
    MediaFile.objects.create(
        pk=14000,
        media_path=paths[52],
        filename="sample-4472s-episode.mp4",
        display_name="existing collision",
    )
    before = {
        media_file_id: MediaFile.objects.get(pk=media_file_id).filename
        for media_file_id in (4278, 4472)
    }

    with pytest.raises(RuntimeError, match="filename repair collision"):
        _run_migration()

    assert {
        media_file_id: MediaFile.objects.get(pk=media_file_id).filename
        for media_file_id in (4278, 4472)
    } == before


@pytest.mark.django_db(transaction=True)
def test_migration_aborts_on_collisions_between_planned_normalizations():
    _create_targets()
    MediaFile.objects.filter(pk=4278).update(filename="planned'-name.mp4")
    MediaFile.objects.filter(pk=4472).update(filename="planned-name'.mp4")
    earlier_valid_target = MediaFile.objects.get(pk=1468)
    earlier_valid_filename = earlier_valid_target.filename

    with pytest.raises(RuntimeError, match="filename repair collision"):
        _run_migration()

    assert MediaFile.objects.get(pk=4278).filename == "planned'-name.mp4"
    assert MediaFile.objects.get(pk=4472).filename == "planned-name'.mp4"
    assert MediaFile.objects.get(pk=1468).filename == earlier_valid_filename


def test_migration_is_irreversible():
    migration = MIGRATION.Migration(
        "0077_repair_local_mediafile_filenames", "mediaviewer"
    )
    assert migration.operations[0].reversible is False
