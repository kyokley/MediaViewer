import importlib
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from mediaviewer.models import (
    Comment,
    DownloadToken,
    Genre,
    MediaFile,
    MediaPath,
    Movie,
    Poster,
    TV,
    VideoProgress,
)


MIGRATION = importlib.import_module(
    "mediaviewer.migrations.0076_remove_duplicate_local_mediafiles"
)
CASES = (
    (
        288,
        "episode-one.mp4",
        7999,
        8001,
    ),
    (
        378,
        "episode-two.mp4",
        9955,
        9956,
    ),
)


@pytest.mark.django_db(transaction=True)
def test_migration_removes_only_confirmed_old_local_duplicates_and_owned_rows():
    user = get_user_model().objects.create_user(username="migration-test")
    tv = TV.objects.create(name="migration test show")
    path = MediaPath.objects.create(pk=288, tv=tv, _path="/local/show")
    duplicate_poster = Poster.objects.create(episodename="duplicate poster")
    shared_poster = Poster.objects.create(episodename="shared poster")
    genre = Genre.objects.create(genre="retained genre")
    duplicate_poster.genres.add(genre)
    targets = []
    for path_id, filename, loser_id, keeper_id in CASES:
        filename = f"episode-{path_id}.mp4"
        media_path = (
            path
            if path_id == 288
            else MediaPath.objects.create(
                pk=path_id, tv=tv, _path=f"/local/show-{path_id}"
            )
        )
        duplicate = MediaFile.objects.create(
            pk=loser_id,
            media_path=media_path,
            filename=filename,
            display_name="duplicate",
            _poster=duplicate_poster if path_id == 288 else None,
        )
        keeper = MediaFile.objects.create(
            pk=keeper_id,
            media_path=media_path,
            filename=filename,
            display_name="keeper",
            _poster=shared_poster if path_id == 288 else None,
        )
        targets.append((duplicate, keeper))

    unrelated_path = MediaPath.objects.create(pk=500, tv=tv, _path="/local/other")
    unrelated = MediaFile.objects.create(
        pk=12000,
        media_path=unrelated_path,
        filename="same-name-but-out-of-scope.mkv",
        display_name="unrelated",
    )
    unrelated_duplicate = MediaFile.objects.create(
        pk=12001,
        media_path=unrelated_path,
        filename="same-name-but-out-of-scope.mkv",
        display_name="unrelated duplicate",
    )
    Comment.objects.create(user=user, media_file=targets[0][0], viewed=True)
    keeper_comment = Comment.objects.create(
        user=user, media_file=targets[0][1], viewed=False
    )
    VideoProgress.objects.create(
        user=user,
        filename=targets[0][0].filename,
        hashed_filename="duplicate-progress",
        offset=1,
        media_file=targets[0][0],
    )
    keeper_progress = VideoProgress.objects.create(
        user=user,
        filename=targets[0][1].filename,
        hashed_filename="keeper-progress",
        offset=2,
        media_file=targets[0][1],
    )
    DownloadToken.objects.create(
        user=user,
        path="/local/show",
        filename=targets[0][0].filename,
        displayname="duplicate token",
        media_file=targets[0][0],
    )
    keeper_token = DownloadToken.objects.create(
        user=user,
        path="/local/show",
        filename=targets[0][1].filename,
        displayname="keeper token",
        media_file=targets[0][1],
    )

    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0075_mediapath_migration_source")]
    )
    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)
    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)

    for duplicate, keeper in targets:
        assert not MediaFile.objects.filter(pk=duplicate.pk).exists()
        assert MediaFile.objects.filter(pk=keeper.pk).exists()
    assert MediaFile.objects.filter(pk=unrelated.pk).exists()
    assert MediaFile.objects.filter(pk=unrelated_duplicate.pk).exists()
    assert not Comment.objects.filter(media_file_id=targets[0][0].pk).exists()
    assert not VideoProgress.objects.filter(media_file_id=targets[0][0].pk).exists()
    assert not DownloadToken.objects.filter(media_file_id=targets[0][0].pk).exists()
    assert Comment.objects.get(pk=keeper_comment.pk).media_file_id == targets[0][1].pk
    assert (
        VideoProgress.objects.get(pk=keeper_progress.pk).media_file_id
        == targets[0][1].pk
    )
    assert (
        DownloadToken.objects.get(pk=keeper_token.pk).media_file_id == targets[0][1].pk
    )
    assert (
        keeper_comment.user_id
        == keeper_progress.user_id
        == keeper_token.user_id
        == user.pk
    )
    assert not Poster.objects.filter(pk=duplicate_poster.pk).exists()
    assert Poster.objects.filter(pk=shared_poster.pk).exists()
    assert Genre.objects.filter(pk=genre.pk).exists()
    assert not duplicate_poster.genres.through.objects.filter(
        poster_id=duplicate_poster.pk
    ).exists()
    assert MediaPath.objects.filter(pk__in=(288, 378, 500)).count() == 3
    assert TV.objects.filter(pk=tv.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_migration_is_safe_when_target_rows_are_already_absent():
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0075_mediapath_migration_source")]
    )
    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)


@pytest.mark.django_db(transaction=True)
def test_migration_leaves_a_partially_absent_pair_untouched():
    path_id, filename, loser_id, _ = CASES[0]
    tv = TV.objects.create(name="partial pair show")
    path = MediaPath.objects.create(pk=path_id, tv=tv, _path="/local/partial")
    MediaFile.objects.create(
        pk=loser_id,
        media_path=path,
        filename=filename,
        display_name="remaining row",
    )
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0075_mediapath_migration_source")]
    )

    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)

    assert MediaFile.objects.filter(pk=loser_id).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("case_index", [0, 1])
def test_migration_aborts_if_a_confirmed_row_has_changed(case_index):
    path_id, filename, loser_id, keeper_id = CASES[case_index]
    tv = TV.objects.create(name="guard test show")
    path = MediaPath.objects.create(pk=path_id, tv=tv, _path="/local/guard")
    MediaFile.objects.create(
        pk=loser_id,
        media_path=path,
        filename=filename,
        display_name="loser",
    )
    MediaFile.objects.create(
        pk=keeper_id,
        media_path=path,
        filename="changed filename",
        display_name="keeper",
    )
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0075_mediapath_migration_source")]
    )

    with pytest.raises(RuntimeError, match="changed since confirmation"):
        with executor.connection.schema_editor() as schema_editor:
            MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)
    assert MediaFile.objects.filter(pk__in=(loser_id, keeper_id)).count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("source_path", "child_b2_uuid"),
    [("/local/guard-b2", True), ("b2://bucket/path", False), ("", False)],
    ids=("child-b2-uuid", "b2-parent-path", "empty-parent-path"),
)
def test_migration_aborts_if_a_confirmed_row_is_not_local(source_path, child_b2_uuid):
    path_id, filename, loser_id, keeper_id = CASES[0]
    tv = TV.objects.create(name="remote guard show")
    path = MediaPath.objects.create(pk=path_id, tv=tv, _path=source_path)
    MediaFile.objects.create(
        pk=loser_id,
        media_path=path,
        filename=filename,
        display_name="loser",
    )
    MediaFile.objects.create(
        pk=keeper_id,
        media_path=path,
        filename=filename,
        display_name="keeper",
        b2_uuid=uuid.uuid4() if child_b2_uuid else None,
    )
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0075_mediapath_migration_source")]
    )

    with pytest.raises(RuntimeError, match="changed since confirmation"):
        with executor.connection.schema_editor() as schema_editor:
            MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)
    assert MediaFile.objects.filter(pk__in=(loser_id, keeper_id)).count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("shared_reference", ["tv", "movie"])
def test_migration_retains_a_loser_poster_shared_with_parent_media(shared_reference):
    path_id, filename, loser_id, keeper_id = CASES[0]
    tv = TV.objects.create(name="shared poster source show")
    path = MediaPath.objects.create(pk=path_id, tv=tv, _path="/local/shared-poster")
    poster = Poster.objects.create(episodename="shared loser poster")
    loser = MediaFile.objects.create(
        pk=loser_id,
        media_path=path,
        filename=filename,
        display_name="loser",
        _poster=poster,
    )
    MediaFile.objects.create(
        pk=keeper_id,
        media_path=path,
        filename=filename,
        display_name="keeper",
    )
    if shared_reference == "tv":
        referenced_media = TV.objects.create(name="poster-sharing show", _poster=poster)
    else:
        referenced_media = Movie.objects.create(
            name="poster-sharing movie", _poster=poster
        )
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0075_mediapath_migration_source")]
    )

    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.remove_confirmed_duplicates(state.apps, schema_editor)

    assert not MediaFile.objects.filter(pk=loser.pk).exists()
    assert Poster.objects.filter(pk=poster.pk).exists()
    referenced_media.refresh_from_db()
    assert referenced_media._poster_id == poster.pk


def test_migration_is_irreversible():
    migration = MIGRATION.Migration(
        "0076_remove_duplicate_local_mediafiles", "mediaviewer"
    )
    assert migration.operations[0].reversible is False
