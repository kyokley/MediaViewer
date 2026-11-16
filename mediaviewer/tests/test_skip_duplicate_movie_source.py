import hashlib
import importlib
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from mediaviewer.models import (
    Collection,
    Comment,
    DownloadToken,
    MediaFile,
    MediaPath,
    Movie,
    Poster,
    TV,
    VideoProgress,
)


MIGRATION = importlib.import_module(
    "mediaviewer.migrations.0078_skip_duplicate_movie_source"
)
STALE_PATH = "/synthetic/stale-source"
CANONICAL_PATH = "/synthetic/canonical-source"


def _hash(path):
    return hashlib.sha256(path.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def synthetic_path_fingerprints(monkeypatch):
    monkeypatch.setattr(
        MIGRATION, "STALE_PATH_SHA256", _hash(STALE_PATH), raising=False
    )
    monkeypatch.setattr(
        MIGRATION, "CANONICAL_PATH_SHA256", _hash(CANONICAL_PATH), raising=False
    )


def _run_migration():
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0077_repair_local_mediafile_filenames")]
    )
    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.skip_duplicate_movie_source(state.apps, schema_editor)


def _catalog(*, stale_path=STALE_PATH, canonical_path=CANONICAL_PATH):
    stale_poster = Poster.objects.create(
        tmdb="synthetic-id", release_date=date(2000, 1, 2)
    )
    canonical_poster = Poster.objects.create(
        tmdb="synthetic-id", release_date=date(2000, 1, 2)
    )
    stale_movie = Movie.objects.create(
        pk=165, name="Synthetic Movie", _poster=stale_poster
    )
    canonical_movie = Movie.objects.create(
        pk=328, name="Synthetic Movie", _poster=canonical_poster
    )
    stale = MediaPath.objects.create(
        pk=560, movie=stale_movie, _path=stale_path, filename=None
    )
    canonical = MediaPath.objects.create(
        pk=723, movie=canonical_movie, _path=canonical_path, filename=None
    )
    return stale_movie, canonical_movie, stale, canonical


def _related_rows(movies):
    user = get_user_model().objects.create_user(username="duplicate-source-test")
    rows = []
    for index, movie in enumerate(movies):
        rows.append(Comment.objects.create(user=user, movie=movie, viewed=bool(index)))
        rows.append(
            VideoProgress.objects.create(
                user=user,
                movie=movie,
                filename=f"synthetic-progress-{index}",
                hashed_filename=f"synthetic-hash-{index}",
                offset=1.25 + index,
            )
        )
        rows.append(
            DownloadToken.objects.create(
                user=user,
                movie=movie,
                path=f"/synthetic/token-{index}",
                filename=f"synthetic-token-{index}",
                displayname=f"Synthetic {index}",
            )
        )
    return rows


def _row_values(rows):
    return [
        (row.__class__, row.pk, row.__class__.objects.filter(pk=row.pk).values().get())
        for row in rows
    ]


def _assert_rows_unchanged(before):
    for model, pk, values in before:
        assert model.objects.filter(pk=pk).values().get() == values


@pytest.mark.django_db(transaction=True)
def test_migration_skips_only_stale_path_preserving_catalog_and_related_rows():
    stale_movie, canonical_movie, stale, canonical = _catalog()
    collection = Collection.objects.create(name="synthetic collection")
    stale_movie.collections.add(collection)
    canonical_movie.collections.add(collection)
    related = _related_rows((stale_movie, canonical_movie))
    movies_before = {
        movie.pk: Movie.objects.filter(pk=movie.pk).values().get()
        for movie in (stale_movie, canonical_movie)
    }
    posters_before = {
        poster.pk: Poster.objects.filter(pk=poster.pk).values().get()
        for poster in (stale_movie._poster, canonical_movie._poster)
    }
    collection_links_before = list(
        Movie.collections.through.objects.order_by("movie_id").values()
    )
    related_before = _row_values(related)
    stale_before = MediaPath.objects.filter(pk=560).values().get()
    canonical_before = MediaPath.objects.filter(pk=723).values().get()

    _run_migration()
    _run_migration()

    assert MediaPath.objects.filter(pk=560).values().get() == {
        **stale_before,
        "skip": True,
    }
    assert MediaPath.objects.filter(pk=723).values().get() == canonical_before
    assert {
        movie_id: Movie.objects.filter(pk=movie_id).values().get()
        for movie_id in movies_before
    } == movies_before
    assert {
        poster_id: Poster.objects.filter(pk=poster_id).values().get()
        for poster_id in posters_before
    } == posters_before
    assert (
        list(Movie.collections.through.objects.order_by("movie_id").values())
        == collection_links_before
    )
    _assert_rows_unchanged(related_before)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("state", ["missing", "already-skipped", "b2"])
def test_migration_noops_for_missing_skipped_or_published_stale_source(state):
    if state == "missing":
        _run_migration()
        assert not MediaPath.objects.filter(pk=560).exists()
        return
    stale_path = "b2://synthetic-bucket/published" if state == "b2" else STALE_PATH
    _, _, stale, _ = _catalog(stale_path=stale_path)
    if state == "already-skipped":
        stale.skip = True
        stale.save(update_fields=["skip"])
    before = MediaPath.objects.filter(pk=560).values().get()
    _run_migration()
    assert MediaPath.objects.filter(pk=560).values().get() == before


@pytest.mark.django_db(transaction=True)
def test_migration_accepts_published_canonical_source():
    _, _, stale, canonical = _catalog(canonical_path="b2://synthetic-bucket/object")
    canonical.filename = "synthetic-remote.mp4"
    canonical.save(update_fields=["filename"])

    _run_migration()

    stale.refresh_from_db()
    canonical.refresh_from_db()
    assert stale.skip is True
    assert canonical._path == "b2://synthetic-bucket/object"
    assert canonical.filename == "synthetic-remote.mp4"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "scenario",
    [
        "path-fingerprint",
        "wrong-movie",
        "tv-owned",
        "filename",
        "migration-source",
        "mediafile",
        "migration-target",
    ],
)
def test_migration_rejects_stale_source_changes(scenario):
    stale_path = (
        "/synthetic/changed-source" if scenario == "path-fingerprint" else STALE_PATH
    )
    stale_movie, _, stale, _ = _catalog(stale_path=stale_path)
    if scenario == "wrong-movie":
        Movie.objects.create(pk=166, name="Synthetic Movie")
        stale.movie_id = 166
        stale.save(update_fields=["movie"])
    elif scenario == "tv-owned":
        tv = TV.objects.create(name="Synthetic TV")
        stale.movie = None
        stale.tv = tv
        stale.save(update_fields=["movie", "tv"])
    elif scenario == "filename":
        stale.filename = "synthetic.mp4"
        stale.save(update_fields=["filename"])
    elif scenario == "migration-source":
        stale.migration_source = MediaPath.objects.create(_path="/synthetic/source")
        stale.save(update_fields=["migration_source"])
    elif scenario == "mediafile":
        MediaFile.objects.create(media_path=stale, filename="synthetic.mp4")
    elif scenario == "migration-target":
        MediaPath.objects.create(_path="/synthetic/target", migration_source=stale)
    before = MediaPath.objects.filter(pk=560).values().get()

    with pytest.raises(RuntimeError, match="MediaPath 560"):
        _run_migration()

    assert MediaPath.objects.filter(pk=560).values().get() == before


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "scenario",
    [
        "missing",
        "disabled",
        "wrong-owner",
        "not-highest",
        "path-fingerprint",
        "migration-source",
        "mediafile",
    ],
)
def test_migration_rejects_invalid_canonical_source(scenario):
    _, canonical_movie, _, canonical = _catalog(
        canonical_path=(
            "/synthetic/changed-canonical"
            if scenario == "path-fingerprint"
            else CANONICAL_PATH
        )
    )
    if scenario == "missing":
        canonical.delete()
    elif scenario == "disabled":
        canonical.skip = True
        canonical.save(update_fields=["skip"])
    elif scenario == "wrong-owner":
        other_movie = Movie.objects.create(pk=329, name="Other synthetic movie")
        canonical.movie = other_movie
        canonical.save(update_fields=["movie"])
    elif scenario == "not-highest":
        MediaPath.objects.create(
            pk=724, movie=canonical_movie, _path="/synthetic/newer"
        )
    elif scenario == "migration-source":
        canonical.migration_source = MediaPath.objects.create(
            _path="/synthetic/canonical-parent"
        )
        canonical.save(update_fields=["migration_source"])
    elif scenario == "mediafile":
        MediaFile.objects.create(media_path=canonical, filename="synthetic.mp4")
    before = MediaPath.objects.filter(pk=560).values().get()

    with pytest.raises(RuntimeError, match="MediaPath 560|MediaPath 723"):
        _run_migration()

    assert MediaPath.objects.filter(pk=560).values().get() == before


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mismatch", ["tmdb", "release-date", "missing-poster"])
def test_migration_rejects_unconfirmed_shared_movie_metadata(mismatch):
    stale_movie, canonical_movie, _, _ = _catalog()
    if mismatch == "tmdb":
        canonical_movie._poster.tmdb = "different-id"
        canonical_movie._poster.save(update_fields=["tmdb"])
    elif mismatch == "release-date":
        canonical_movie._poster.release_date = date(2001, 2, 3)
        canonical_movie._poster.save(update_fields=["release_date"])
    else:
        stale_movie._poster.delete()
        stale_movie._poster = None
        stale_movie.save(update_fields=["_poster"])
    before = MediaPath.objects.filter(pk=560).values().get()

    with pytest.raises(RuntimeError, match="Movies 165 and 328"):
        _run_migration()

    assert MediaPath.objects.filter(pk=560).values().get() == before


def test_migration_is_irreversible():
    migration = MIGRATION.Migration("0078_skip_duplicate_movie_source", "mediaviewer")
    assert migration.operations[0].reversible is False
