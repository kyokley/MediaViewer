import uuid
import base64

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse

from mediaviewer.models import MediaFile, MediaPath, MigrationOwnership


@pytest.mark.django_db
def test_new_file_routes_reject_anonymous_and_nonstaff(client, create_user):
    routes = (
        reverse("mediaviewer:api:migrations-file-candidates"),
        reverse("mediaviewer:api:migrations-prepare-file", args=[1]),
        reverse("mediaviewer:api:migrations-publish-file", args=[1]),
    )
    for user in (None, create_user(is_staff=False)):
        client.logout()
        if user:
            client.force_login(user)
        assert client.get(routes[0]).status_code in (401, 403)
        assert client.post(
            routes[1], {}, content_type="application/json"
        ).status_code in (
            401,
            403,
        )
        assert client.post(
            routes[2], {}, content_type="application/json"
        ).status_code in (
            401,
            403,
        )


@pytest.mark.django_db
def test_waiter_basic_auth_backend_can_access_file_candidates(client, settings):
    settings.WAITER_LOGIN = "waiter"
    settings.WAITER_PASSWORD_HASH = make_password("test-secret")
    credentials = base64.b64encode(b"waiter:test-secret").decode("ascii")
    client.defaults["HTTP_AUTHORIZATION"] = f"Basic {credentials}"
    response = client.get(reverse("mediaviewer:api:migrations-file-candidates"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_file_candidates_paginate_individual_hidden_tv_children(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    first = create_tv_media_file(filename="Show.S01E01.mp4")
    second = MediaFile.objects.create(
        media_path=first.media_path,
        filename="Show.S01E02.mp4",
        display_name="2",
        hide=True,
    )
    third = MediaFile.objects.create(
        media_path=first.media_path, filename="Show.S01E03.mp4", display_name="3"
    )
    client.force_login(create_user(is_staff=True))
    url = reverse("mediaviewer:api:migrations-file-candidates")
    page = client.get(url, {"limit": 1}).json()
    ids = [page["candidates"][0]["mediafile_pk"]]
    while page["next_cursor"]:
        page = client.get(url, {"limit": 1, "cursor": page["next_cursor"]}).json()
        ids.extend(row["mediafile_pk"] for row in page["candidates"])
    assert ids == [first.pk, second.pk, third.pk]


@pytest.mark.django_db
def test_tv_file_prepare_publish_moves_only_selected_child_and_replays(
    client, create_user, create_tv_media_file, settings, mocker
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    first = create_tv_media_file(filename="Show.S01E01.mp4")
    source_pk = first.media_path_id
    sibling = MediaFile.objects.create(
        media_path=first.media_path, filename="Show.S01E02.mp4", display_name="2"
    )
    third = MediaFile.objects.create(
        media_path=first.media_path,
        filename="Show.S01E03.mp4",
        display_name="3",
        hide=True,
    )
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = uuid.uuid4()
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    initial_candidates = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"]
    candidate = next(
        row for row in initial_candidates if row["mediafile_pk"] == first.pk
    )
    second_candidate = next(
        row for row in initial_candidates if row["mediafile_pk"] == sibling.pk
    )
    manifest = {
        "pk": first.pk,
        "filename": first.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 100,
        "sha1": "a" * 40,
        "subtitles": [{"filename": f"{uuid.uuid4()}.vtt", "size": 0, "sha1": "b" * 40}],
    }
    prepare_url = reverse(
        "mediaviewer:api:migrations-prepare-file", args=[first.media_path_id]
    )
    prepared = client.post(
        prepare_url,
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": manifest},
        content_type="application/json",
    )
    assert prepared.status_code == 200, prepared.content
    assert not first.media_path.is_b2
    target = MediaPath.objects.get(pk=prepared.json()["target_pk"])
    assert target.tv_id is None and target.movie_id is None
    padded_id = f"{target.pk:09d}"
    expected_prefix = (
        "tv/" + "/".join(padded_id[i : i + 3] for i in range(0, 9, 3)) + "/"
    )
    assert (
        prepared.json()["b2_upload_prefix"]
        == target.b2_upload_prefix
        == expected_prefix
    )
    publish_url = reverse(
        "mediaviewer:api:migrations-publish-file", args=[first.media_path_id]
    )
    body = {"run_id": str(run_id), "prepared": prepared.json()["prepared"]}
    response = client.post(publish_url, body, content_type="application/json")
    assert response.status_code == 200, response.content
    first.refresh_from_db()
    sibling.refresh_from_db()
    third.refresh_from_db()
    assert first.media_path_id == response.json()["media_path_pk"]
    assert first.b2_uuid == uuid.UUID(manifest["b2_uuid"])
    assert sibling.media_path_id != first.media_path_id
    assert sibling.media_path_id == third.media_path_id == source_pk
    assert sibling.media_path._path == third.media_path._path
    assert sibling.hide is False and third.hide is True
    mocker.patch.object(
        MediaPath, "b2_uuid_presigned_url", return_value="b2-presigned-token"
    )
    assert first.downloadLink("episode-guid") == "b2-presigned-token"
    assert sibling.downloadLink("episode-guid") != "b2-presigned-token"
    first_prepared = prepared.json()
    settings.B2_BUCKET_NAME = "changed-bucket"
    second_file = {
        "pk": sibling.pk,
        "filename": sibling.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 101,
        "sha1": "d" * 40,
        "subtitles": [],
    }
    second_prepared = client.post(
        prepare_url,
        {
            "run_id": str(run_id),
            "snapshot": second_candidate["snapshot"],
            "file": second_file,
        },
        content_type="application/json",
    )
    assert second_prepared.status_code == 200
    assert second_prepared.json()["target_pk"] == first_prepared["target_pk"]
    assert second_prepared.json()["bucket"] == first_prepared["bucket"] == "archive"
    assert (
        second_prepared.json()["b2_upload_prefix"] == first_prepared["b2_upload_prefix"]
    )
    published_second = client.post(
        publish_url,
        {"run_id": str(run_id), "prepared": second_prepared.json()["prepared"]},
        content_type="application/json",
    )
    assert published_second.status_code == 200
    sibling.refresh_from_db()
    third.refresh_from_db()
    assert sibling.media_path_id == first.media_path_id
    assert third.media_path_id == source_pk
    replay = client.post(publish_url, body, content_type="application/json")
    assert replay.status_code == 200
    assert replay.json() == response.json()
    assert MigrationOwnership.objects.get(pk=1).owner_id == owner.pk


@pytest.mark.django_db
@pytest.mark.parametrize("existing_child", (False, True))
def test_movie_file_migration_updates_parent_and_keeps_child_identity(
    client, create_user, create_movie, settings, existing_child
):
    settings.B2_BUCKET_NAME = "archive"
    movie = create_movie()
    parent = movie.mediapath_set.get()
    child = (
        MediaFile.objects.create(
            media_path=parent, filename="Film.mkv", display_name="Original"
        )
        if existing_child
        else None
    )
    client.force_login(create_user(is_staff=True))
    run_id = uuid.uuid4()
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    manifest = {
        "pk": child.pk if child else None,
        "filename": child.filename if child else "Film.mkv",
        "b2_uuid": str(uuid.uuid4()),
        "size": 20,
        "sha1": "c" * 40,
        "subtitles": [],
    }
    prepared = client.post(
        reverse("mediaviewer:api:migrations-prepare-file", args=[parent.pk]),
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": manifest},
        content_type="application/json",
    )
    assert prepared.status_code == 200, prepared.content
    assert prepared.json()["bucket"] == "archive"
    assert parent.is_b2 is False
    result = client.post(
        reverse("mediaviewer:api:migrations-publish-file", args=[parent.pk]),
        {"run_id": str(run_id), "prepared": prepared.json()["prepared"]},
        content_type="application/json",
    )
    assert result.status_code == 200, result.content
    parent.refresh_from_db()
    assert parent.is_b2
    child = MediaFile.objects.get(media_path=parent)
    assert child.pk == (result.json()["mediafile_pk"])
    assert (existing_child and child.display_name == "Original") or not existing_child


@pytest.mark.django_db
@pytest.mark.parametrize("insert_before", ("prepare", "publish"))
@pytest.mark.parametrize("existing_child", (False, True))
def test_movie_membership_change_rejects_prepare_or_publish(
    client, create_user, create_movie, settings, insert_before, existing_child
):
    settings.B2_BUCKET_NAME = "archive"
    parent = create_movie().mediapath_set.get()
    existing = (
        MediaFile.objects.create(media_path=parent, filename="Film.mkv")
        if existing_child
        else None
    )
    client.force_login(create_user(is_staff=True))
    run_id = uuid.uuid4()
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    manifest = {
        "pk": existing.pk if existing else None,
        "filename": existing.filename if existing else "Film.mkv",
        "b2_uuid": str(uuid.uuid4()),
        "size": 20,
        "sha1": "c" * 40,
        "subtitles": [],
    }
    if insert_before == "prepare":
        MediaFile.objects.create(media_path=parent, filename="Intruder.mkv")
    prepared = client.post(
        reverse("mediaviewer:api:migrations-prepare-file", args=[parent.pk]),
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": manifest},
        content_type="application/json",
    )
    if insert_before == "prepare":
        assert prepared.status_code == 409
        return
    assert prepared.status_code == 200, prepared.content
    MediaFile.objects.create(media_path=parent, filename="Intruder.mkv")
    response = client.post(
        reverse("mediaviewer:api:migrations-publish-file", args=[parent.pk]),
        {"run_id": str(run_id), "prepared": prepared.json()["prepared"]},
        content_type="application/json",
    )
    assert response.status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mutation", ("skip", "path", "filename", "subtitles", "wrong_tv", "movie")
)
def test_publish_rejects_tampered_tv_reservation(
    client, create_user, create_tv_media_file, create_movie, settings, mutation
):
    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    run_id = uuid.uuid4()
    client.force_login(create_user(is_staff=True))
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = next(
        row
        for row in client.get(
            reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
        ).json()["candidates"]
        if row["mediafile_pk"] == episode.pk
    )
    file = {
        "pk": episode.pk,
        "filename": episode.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 2,
        "sha1": "a" * 40,
        "subtitles": [],
    }
    prepared = client.post(
        reverse(
            "mediaviewer:api:migrations-prepare-file", args=[episode.media_path_id]
        ),
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": file},
        content_type="application/json",
    ).json()
    target = MediaPath.objects.get(pk=prepared["target_pk"])
    if mutation == "skip":
        target.skip = True
        target.save(update_fields=("skip",))
    elif mutation == "path":
        target._path += "changed/"
        target.save(update_fields=("_path",))
    elif mutation == "filename":
        target.filename = "unexpected.mp4"
        target.save(update_fields=("filename",))
    elif mutation == "subtitles":
        target.subtitle_files = ["unexpected.vtt"]
        target.save(update_fields=("subtitle_files",))
    elif mutation == "wrong_tv":
        other_tv = create_tv_media_file(filename="Other.S01E01.mp4").media_path.tv
        target.tv = other_tv
        target.save(update_fields=("tv",))
    else:
        target.movie = create_movie()
        target.save(update_fields=("movie",))
    response = client.post(
        reverse(
            "mediaviewer:api:migrations-publish-file", args=[episode.media_path_id]
        ),
        {"run_id": str(run_id), "prepared": prepared["prepared"]},
        content_type="application/json",
    )
    assert response.status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize("field,value", (("filename", "Changed.mp4"), ("hide", True)))
def test_exact_replay_rejects_changed_preserved_child_metadata(
    client, create_user, create_tv_media_file, settings, field, value
):
    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    run_id = uuid.uuid4()
    client.force_login(create_user(is_staff=True))
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    file = {
        "pk": episode.pk,
        "filename": episode.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 2,
        "sha1": "a" * 40,
        "subtitles": [],
    }
    url = reverse(
        "mediaviewer:api:migrations-prepare-file", args=[episode.media_path_id]
    )
    prepared = client.post(
        url,
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": file},
        content_type="application/json",
    ).json()
    publish_url = reverse(
        "mediaviewer:api:migrations-publish-file", args=[episode.media_path_id]
    )
    body = {"run_id": str(run_id), "prepared": prepared["prepared"]}
    assert (
        client.post(publish_url, body, content_type="application/json").status_code
        == 200
    )
    MediaFile.objects.filter(pk=episode.pk).update(**{field: value})
    assert (
        client.post(publish_url, body, content_type="application/json").status_code
        == 409
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    (
        ("filename", "Changed.mp4"),
        ("subtitle_files", ["changed.vtt"]),
        ("skip", True),
    ),
)
def test_exact_movie_replay_rejects_changed_parent_metadata(
    client, create_user, create_movie, settings, field, value
):
    settings.B2_BUCKET_NAME = "archive"
    parent = create_movie().mediapath_set.get()
    run_id = uuid.uuid4()
    client.force_login(create_user(is_staff=True))
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    file = {
        "pk": None,
        "filename": "Film.mkv",
        "b2_uuid": str(uuid.uuid4()),
        "size": 3,
        "sha1": "e" * 40,
        "subtitles": [],
    }
    prepared = client.post(
        reverse("mediaviewer:api:migrations-prepare-file", args=[parent.pk]),
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": file},
        content_type="application/json",
    ).json()
    url = reverse("mediaviewer:api:migrations-publish-file", args=[parent.pk])
    body = {"run_id": str(run_id), "prepared": prepared["prepared"]}
    assert client.post(url, body, content_type="application/json").status_code == 200
    MediaPath.objects.filter(pk=parent.pk).update(**{field: value})
    assert client.post(url, body, content_type="application/json").status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filename", ("../escape.mp4", "a\\b.mp4", "bad\x00name.mp4", "x" * 257 + ".mp4")
)
def test_prepare_rejects_malformed_file_object_and_unsafe_filenames(
    client, create_user, create_tv_media_file, settings, filename
):
    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    run_id = uuid.uuid4()
    client.force_login(create_user(is_staff=True))
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    file = {
        "pk": episode.pk,
        "filename": filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 3,
        "sha1": "f" * 40,
        "subtitles": [],
    }
    url = reverse(
        "mediaviewer:api:migrations-prepare-file", args=[episode.media_path_id]
    )
    malformed = client.post(
        url,
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": []},
        content_type="application/json",
    )
    assert malformed.status_code == 400
    response = client.post(
        url,
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": file},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_publish_rejects_wrong_run_owner_route_and_stale_source(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = uuid.uuid4()
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    file = {
        "pk": episode.pk,
        "filename": episode.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 3,
        "sha1": "a" * 40,
        "subtitles": [],
    }
    prepared = client.post(
        reverse(
            "mediaviewer:api:migrations-prepare-file", args=[episode.media_path_id]
        ),
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": file},
        content_type="application/json",
    ).json()["prepared"]
    url = reverse(
        "mediaviewer:api:migrations-publish-file", args=[episode.media_path_id]
    )
    assert (
        client.post(
            url,
            {"run_id": str(uuid.uuid4()), "prepared": prepared},
            content_type="application/json",
        ).status_code
        == 409
    )
    wrong_route = reverse(
        "mediaviewer:api:migrations-publish-file", args=[episode.media_path_id + 1000]
    )
    assert (
        client.post(
            wrong_route,
            {"run_id": str(run_id), "prepared": prepared},
            content_type="application/json",
        ).status_code
        == 409
    )
    client.force_login(create_user(is_staff=True))
    assert (
        client.post(
            url,
            {"run_id": str(run_id), "prepared": prepared},
            content_type="application/json",
        ).status_code
        == 409
    )
    client.force_login(owner)
    MediaPath.objects.filter(pk=episode.media_path_id).update(skip=True)
    response = client.post(
        url,
        {"run_id": str(run_id), "prepared": prepared},
        content_type="application/json",
    )
    assert response.status_code == 409
    episode.refresh_from_db()
    assert episode.b2_uuid is None


@pytest.mark.django_db
def test_prepare_rejects_duplicate_uuid_and_reservation_path_collision(
    client, create_user, create_tv_media_file, settings
):
    from mediaviewer.api.file_migration import _target

    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    duplicate = create_tv_media_file(filename="Other.S01E01.mp4")
    run_id = uuid.uuid4()
    client.force_login(create_user(is_staff=True))
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidates = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"]
    candidate = next(
        row for row in candidates if row["source_pk"] == episode.media_path_id
    )
    manifest = {
        "pk": episode.pk,
        "filename": episode.filename,
        "b2_uuid": str(duplicate.b2_uuid or uuid.uuid4()),
        "size": 2,
        "sha1": "b" * 40,
        "subtitles": [],
    }
    duplicate.b2_uuid = uuid.uuid4()
    duplicate.save(update_fields=("b2_uuid",))
    manifest["b2_uuid"] = str(duplicate.b2_uuid)
    url = reverse(
        "mediaviewer:api:migrations-prepare-file", args=[episode.media_path_id]
    )
    base = {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": manifest}
    assert client.post(url, base, content_type="application/json").status_code == 400
    target = _target(episode.media_path, None, None)
    MediaPath.objects.create(_path=target["path"])
    manifest["b2_uuid"] = str(uuid.uuid4())
    collision = client.post(
        url,
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": manifest},
        content_type="application/json",
    )
    assert collision.status_code == 409
    assert collision.json() == {"error": "Reserved target path is already in use"}


@pytest.mark.django_db
def test_movie_candidate_reports_ambiguous_file_membership(
    client, create_user, create_movie, settings
):
    settings.B2_BUCKET_NAME = "archive"
    parent = create_movie().mediapath_set.get()
    MediaFile.objects.create(media_path=parent, filename="First.mkv")
    MediaFile.objects.create(media_path=parent, filename="Second.mkv")
    client.force_login(create_user(is_staff=True))
    response = client.get(reverse("mediaviewer:api:migrations-file-candidates"))
    assert response.status_code == 409
    assert "ambiguous file membership" in response.json()["error"]


@pytest.mark.django_db
def test_file_publish_rolls_back_target_and_child_on_save_failure(
    client, create_user, create_tv_media_file, settings, mocker
):
    from django.db import IntegrityError

    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    run_id = uuid.uuid4()
    client.force_login(create_user(is_staff=True))
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(run_id), "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-file-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    file = {
        "pk": episode.pk,
        "filename": episode.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 3,
        "sha1": "a" * 40,
        "subtitles": [],
    }
    prepared = client.post(
        reverse(
            "mediaviewer:api:migrations-prepare-file", args=[episode.media_path_id]
        ),
        {"run_id": str(run_id), "snapshot": candidate["snapshot"], "file": file},
        content_type="application/json",
    ).json()
    target = MediaPath.objects.get(pk=prepared["target_pk"])
    mocker.patch.object(
        MediaFile, "save", side_effect=IntegrityError("constraint detail")
    )
    response = client.post(
        reverse(
            "mediaviewer:api:migrations-publish-file", args=[episode.media_path_id]
        ),
        {"run_id": str(run_id), "prepared": prepared["prepared"]},
        content_type="application/json",
    )
    assert response.status_code == 409
    assert "constraint detail" not in response.content.decode()
    episode.refresh_from_db()
    target.refresh_from_db()
    assert episode.media_path_id != target.pk
    assert episode.b2_uuid is None
    assert target.tv_id is None and target.movie_id is None
