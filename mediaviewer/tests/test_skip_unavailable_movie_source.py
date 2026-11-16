import hashlib
import importlib

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
    "mediaviewer.migrations.0079_skip_unavailable_movie_source"
)
SOURCE_PATH = "/synthetic/unavailable-movie-source"


def _hash(path):
    return hashlib.sha256(path.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def synthetic_path_fingerprint(monkeypatch):
    monkeypatch.setattr(
        MIGRATION, "SOURCE_PATH_SHA256", _hash(SOURCE_PATH), raising=False
    )


def _run_migration():
    executor = MigrationExecutor(connection)
    state = executor.loader.project_state(
        [("mediaviewer", "0078_skip_duplicate_movie_source")]
    )
    with executor.connection.schema_editor() as schema_editor:
        MIGRATION.skip_unavailable_movie_source(state.apps, schema_editor)


def _source(*, path=SOURCE_PATH, filename=None, movie_id=37):
    movie = Movie.objects.create(pk=movie_id, name="Synthetic Movie")
    return MediaPath.objects.create(pk=432, movie=movie, _path=path, filename=filename)


def _row_snapshot(model, ids):
    return {pk: model.objects.filter(pk=pk).values().get() for pk in ids}


@pytest.mark.django_db(transaction=True)
def test_migration_skips_only_unavailable_path_and_preserves_movie_history():
    source = _source()
    poster = Poster.objects.create(tmdb="synthetic-tmdb", release_date="2000-01-02")
    source.movie._poster = poster
    source.movie.save(update_fields=["_poster"])
    user = get_user_model().objects.create_user(username="unavailable-source-test")
    comment = Comment.objects.create(user=user, movie=source.movie, viewed=True)
    progress = VideoProgress.objects.create(
        user=user,
        movie=source.movie,
        filename="synthetic-progress-name",
        hashed_filename="synthetic-stable-hash",
        offset=12.5,
    )
    token = DownloadToken.objects.create(
        user=user,
        movie=source.movie,
        path="/synthetic/token-path",
        filename="synthetic-token-name",
        displayname="Synthetic token",
    )
    collection = Collection.objects.create(name="synthetic collection")
    source.movie.collections.add(collection)
    unrelated = MediaPath.objects.create(_path="/synthetic/unrelated")

    source_before = MediaPath.objects.filter(pk=432).values().get()
    movie_before = Movie.objects.filter(pk=37).values().get()
    poster_before = Poster.objects.filter(pk=poster.pk).values().get()
    comment_before = Comment.objects.filter(pk=comment.pk).values().get()
    progress_before = VideoProgress.objects.filter(pk=progress.pk).values().get()
    token_before = DownloadToken.objects.filter(pk=token.pk).values().get()
    collection_links_before = list(
        Movie.collections.through.objects.order_by("movie_id").values()
    )
    unrelated_before = MediaPath.objects.filter(pk=unrelated.pk).values().get()

    _run_migration()
    _run_migration()

    assert MediaPath.objects.filter(pk=432).values().get() == {
        **source_before,
        "skip": True,
    }
    assert Movie.objects.filter(pk=37).values().get() == movie_before
    assert Poster.objects.filter(pk=poster.pk).values().get() == poster_before
    assert Comment.objects.filter(pk=comment.pk).values().get() == comment_before
    assert (
        VideoProgress.objects.filter(pk=progress.pk).values().get() == progress_before
    )
    assert DownloadToken.objects.filter(pk=token.pk).values().get() == token_before
    assert (
        list(Movie.collections.through.objects.order_by("movie_id").values())
        == collection_links_before
    )
    assert MediaPath.objects.filter(pk=unrelated.pk).values().get() == unrelated_before


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("state", ["missing", "already-skipped", "b2"])
def test_migration_noops_for_missing_skipped_or_published_source(state):
    if state == "missing":
        _run_migration()
        assert not MediaPath.objects.filter(pk=432).exists()
        return
    path = "b2://synthetic-bucket/published" if state == "b2" else SOURCE_PATH
    source = _source(path=path)
    if state == "already-skipped":
        source.skip = True
        source.save(update_fields=["skip"])
    before = MediaPath.objects.filter(pk=432).values().get()

    _run_migration()

    assert MediaPath.objects.filter(pk=432).values().get() == before


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "scenario",
    [
        "fingerprint",
        "wrong-movie",
        "tv-owned",
        "explicit-filename",
        "migration-source",
        "mediafile-child",
        "migration-target-child",
        "movie-sibling",
    ],
)
def test_migration_rejects_changed_or_associated_source(scenario):
    path = "/synthetic/changed-source" if scenario == "fingerprint" else SOURCE_PATH
    source = _source(path=path)
    if scenario == "wrong-movie":
        Movie.objects.create(pk=38, name="Other synthetic movie")
        source.movie_id = 38
        source.save(update_fields=["movie"])
    elif scenario == "tv-owned":
        tv = TV.objects.create(name="Synthetic TV")
        source.movie = None
        source.tv = tv
        source.save(update_fields=["movie", "tv"])
    elif scenario == "explicit-filename":
        source.filename = "synthetic.mp4"
        source.save(update_fields=["filename"])
    elif scenario == "migration-source":
        source.migration_source = MediaPath.objects.create(_path="/synthetic/parent")
        source.save(update_fields=["migration_source"])
    elif scenario == "mediafile-child":
        MediaFile.objects.create(media_path=source, filename="synthetic.mp4")
    elif scenario == "migration-target-child":
        MediaPath.objects.create(_path="/synthetic/target", migration_source=source)
    elif scenario == "movie-sibling":
        MediaPath.objects.create(movie=source.movie, _path="/synthetic/sibling")
    before = MediaPath.objects.filter(pk=432).values().get()

    with pytest.raises(RuntimeError, match="MediaPath 432"):
        _run_migration()

    assert MediaPath.objects.filter(pk=432).values().get() == before


def test_migration_is_irreversible():
    migration = MIGRATION.Migration("0079_skip_unavailable_movie_source", "mediaviewer")
    assert migration.operations[0].reversible is False
