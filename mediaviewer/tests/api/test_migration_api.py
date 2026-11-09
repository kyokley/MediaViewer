import uuid

import pytest
from django.urls import reverse

from mediaviewer.models import MediaFile, MediaPath, MigrationOwnership


@pytest.mark.django_db
def test_migration_api_requires_staff(client, create_user):
    user = create_user(is_staff=False)
    client.force_login(user)
    response = client.get(reverse("mediaviewer:api:migrations-candidates"))
    assert response.status_code == 403
    response = client.get(reverse("mediaviewer:api:migrations-run"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_anonymous_and_nonstaff_cannot_read_or_write_migration_routes(
    client, create_user
):
    run_url = reverse("mediaviewer:api:migrations-run")
    candidates_url = reverse("mediaviewer:api:migrations-candidates")
    publish_url = reverse("mediaviewer:api:migrations-publish", args=[1])
    for user in (None, create_user(is_staff=False)):
        client.logout()
        if user:
            client.force_login(user)
        assert client.get(run_url).status_code in (401, 403)
        assert client.get(candidates_url).status_code in (401, 403)
        assert client.post(
            run_url, {}, content_type="application/json"
        ).status_code in (401, 403)
        assert client.delete(
            run_url, {}, content_type="application/json"
        ).status_code in (401, 403)
        assert client.post(
            publish_url, {}, content_type="application/json"
        ).status_code in (401, 403)


@pytest.mark.django_db
def test_candidates_are_ordered_and_include_hidden_children(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    tv_a = create_tv_media_file(filename="A.S01E01.mp4")
    tv_b = create_tv_media_file(filename="B.S01E01.mp4")
    tv_b.hide = True
    tv_b.save(update_fields=("hide",))
    user = create_user(is_staff=True)
    client.force_login(user)

    response = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 1}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["version"] == 1
    candidate = result["candidates"][0]
    assert candidate["pk"] == tv_a.media_path_id
    assert candidate["children"][0]["pk"] == tv_a.pk
    assert candidate["target"]["path"].startswith("b2://archive/tv/")
    padded_id = f"{tv_a.media_path_id:09d}"
    assert (
        candidate["target"]["b2_upload_prefix"]
        == f"tv/{padded_id[:3]}/{padded_id[3:6]}/{padded_id[6:]}/"
    )

    response = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 2}
    )
    assert [row["pk"] for row in response.json()["candidates"]] == sorted(
        [tv_a.media_path_id, tv_b.media_path_id]
    )
    assert response.json()["candidates"][1]["children"][0]["pk"] == tv_b.pk

    assert (
        client.get(
            reverse("mediaviewer:api:migrations-candidates"), {"limit": 1001}
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_candidates_include_malformed_dual_reference_record_in_order(
    client, create_user, create_tv_media_file, create_movie, settings
):
    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    movie = create_movie()
    MediaPath.objects.filter(pk=episode.media_path_id).update(movie_id=movie.pk)
    client.force_login(create_user(is_staff=True))
    response = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 1}
    )
    assert response.status_code == 200
    candidate = response.json()["candidates"][0]
    assert candidate["pk"] == episode.media_path_id
    assert candidate["tv"] is not None
    assert candidate["movie"] == movie.pk


@pytest.mark.django_db
def test_candidates_preserve_null_parent_and_child_metadata(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    episode = create_tv_media_file(filename="Show.S01E01.mp4")
    MediaPath.objects.filter(pk=episode.media_path_id).update(
        filename=None, subtitle_files=None
    )
    MediaFile.objects.filter(pk=episode.pk).update(subtitle_files=None)
    client.force_login(create_user(is_staff=True))
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 1}
    ).json()["candidates"][0]
    assert candidate["filename"] is None
    assert candidate["subtitle_files"] is None
    assert candidate["children"][0]["subtitle_files"] is None


@pytest.mark.django_db
def test_run_status_read_does_not_create_missing_singleton(client, create_user):
    MigrationOwnership.objects.filter(pk=1).delete()
    client.force_login(create_user(is_staff=True))
    response = client.get(reverse("mediaviewer:api:migrations-run"))
    assert response.status_code == 200
    assert response.json() == {"run_id": None, "owner_id": None}
    assert not MigrationOwnership.objects.exists()


@pytest.mark.django_db
def test_run_ownership_is_durable_owner_checked_and_releasable(client, create_user):
    owner = create_user(is_staff=True)
    other = create_user(is_staff=True)
    run_id = str(uuid.uuid4())
    url = reverse("mediaviewer:api:migrations-run")
    client.force_login(owner)
    acquired = client.post(
        url, {"run_id": run_id, "writers_paused": True}, content_type="application/json"
    )
    assert acquired.status_code == 200
    assert acquired.json() == {"acquired": True, "run_id": run_id, "owner_id": owner.pk}
    assert (
        client.post(
            url,
            {"run_id": run_id, "writers_paused": True},
            content_type="application/json",
        ).status_code
        == 200
    )
    assert MigrationOwnership.objects.get(pk=1).owner_id == owner.pk

    client.force_login(other)
    assert (
        client.post(
            url,
            {"run_id": str(uuid.uuid4()), "writers_paused": True},
            content_type="application/json",
        ).status_code
        == 409
    )
    assert (
        client.delete(
            url, {"run_id": run_id}, content_type="application/json"
        ).status_code
        == 409
    )
    client.force_login(owner)
    released = client.delete(url, {"run_id": run_id}, content_type="application/json")
    assert released.status_code == 200
    assert released.json() == {"released": True}
    assert client.delete(
        url, {"run_id": str(uuid.uuid4())}, content_type="application/json"
    ).json() == {"released": True}


@pytest.mark.django_db
def test_run_requires_writers_paused_acknowledgement(client, create_user):
    client.force_login(create_user(is_staff=True))
    response = client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": str(uuid.uuid4()), "writers_paused": False},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_run_id_mismatch_is_conflict_for_current_owner(client, create_user):
    owner = create_user(is_staff=True)
    client.force_login(owner)
    url = reverse("mediaviewer:api:migrations-run")
    active = str(uuid.uuid4())
    client.post(
        url, {"run_id": active, "writers_paused": True}, content_type="application/json"
    )
    response = client.delete(
        url, {"run_id": str(uuid.uuid4())}, content_type="application/json"
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_publish_rejects_stale_snapshot_without_mutation(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    media_file = create_tv_media_file(filename="Show.S01E01.mp4")
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    media_file.hide = True
    media_file.save(update_fields=("hide",))
    url = reverse("mediaviewer:api:migrations-publish", args=[media_file.media_path_id])
    response = client.post(
        url,
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": []},
        content_type="application/json",
    )
    assert response.status_code == 409
    media_file.refresh_from_db()
    assert media_file.b2_uuid is None
    assert not media_file.media_path._path.startswith("b2://")


@pytest.mark.django_db
@pytest.mark.parametrize("change", ("parent", "membership"))
def test_publish_rejects_stale_parent_or_child_membership(
    client, create_user, create_tv_media_file, settings, change
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    media_file = create_tv_media_file(filename="Show.S01E01.mp4")
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    if change == "parent":
        MediaPath.objects.filter(pk=media_file.media_path_id).update(
            filename="changed.mp4"
        )
    else:
        MediaFile.objects.create(
            media_path_id=media_file.media_path_id,
            filename="Show.S01E02.webm",
            display_name="episode",
        )
    url = reverse("mediaviewer:api:migrations-publish", args=[media_file.media_path_id])
    response = client.post(
        url,
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": []},
        content_type="application/json",
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_tv_without_children_cannot_publish(client, create_user, create_tv, settings):
    settings.B2_BUCKET_NAME = "archive"
    tv = create_tv()
    parent = tv.mediapath_set.get()
    client.force_login(create_user(is_staff=True))
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[parent.pk]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": []},
        content_type="application/json",
    )
    assert response.status_code == 400
    parent.refresh_from_db()
    assert not parent.is_b2


@pytest.mark.django_db
def test_tv_rejects_parent_filename_or_malformed_parent_subtitles(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    media_file = create_tv_media_file(filename="Show.S01E01.mp4")
    parent = media_file.media_path
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    # A malformed but falsey-ish JSON value must not be normalized or accepted.
    MediaPath.objects.filter(pk=parent.pk).update(subtitle_files={})
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    assert candidate["subtitle_files"] == {}
    file_payload = {
        "pk": media_file.pk,
        "filename": media_file.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 10,
        "subtitle_files": [],
    }
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[parent.pk]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": [file_payload]},
        content_type="application/json",
    )
    assert response.status_code == 400
    MediaPath.objects.filter(pk=parent.pk).update(
        subtitle_files=[], filename="bad-parent.mp4"
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[parent.pk]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": [file_payload]},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid", ("incomplete", "duplicate", "uuid", "size", "subtitle")
)
def test_tv_rejects_invalid_manifests(
    client, create_user, create_tv_media_file, settings, invalid
):
    settings.B2_BUCKET_NAME = "archive"
    first = create_tv_media_file(filename="Show.S01E01.mp4")
    second = MediaFile.objects.create(
        media_path=first.media_path, filename="Show.S01E02.webm", display_name="Second"
    )
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    files = [
        {
            "pk": first.pk,
            "filename": first.filename,
            "b2_uuid": str(uuid.uuid4()),
            "size": 1,
            "subtitle_files": [],
        },
        {
            "pk": second.pk,
            "filename": second.filename,
            "b2_uuid": str(uuid.uuid4()),
            "size": 2,
            "subtitle_files": [],
        },
    ]
    if invalid == "incomplete":
        files.pop()
    elif invalid == "duplicate":
        files[1]["pk"] = first.pk
    elif invalid == "uuid":
        files[0]["b2_uuid"] = "not-a-uuid"
    elif invalid == "size":
        files[0]["size"] = True
    else:
        files[0]["subtitle_files"] = ["not-a-uuid.vtt"]
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[first.media_path_id]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": files},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not MediaFile.objects.filter(
        pk__in=(first.pk, second.pk), b2_uuid__isnull=False
    ).exists()
    assert not MediaPath.objects.get(pk=first.media_path_id).is_b2


@pytest.mark.django_db
@pytest.mark.parametrize("parent_filename", [None, ""])
def test_tv_publish_updates_all_children_atomically(
    client, create_user, create_tv_media_file, settings, parent_filename
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    first = create_tv_media_file(filename="Show.S01E01.mp4")
    MediaPath.objects.filter(pk=first.media_path_id).update(filename=parent_filename)
    second = MediaFile.objects.create(
        media_path=first.media_path,
        filename="Show.S01E02.webm",
        display_name="Second",
        hide=True,
    )
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    files = [
        {
            "pk": first.pk,
            "filename": first.filename,
            "b2_uuid": str(uuid.uuid4()),
            "size": 10,
            "subtitle_files": [],
        },
        {
            "pk": second.pk,
            "filename": second.filename,
            "b2_uuid": str(uuid.uuid4()),
            "size": 20,
            "subtitle_files": [],
        },
    ]
    url = reverse("mediaviewer:api:migrations-publish", args=[first.media_path_id])
    response = client.post(
        url,
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": files},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.b2_uuid == uuid.UUID(files[0]["b2_uuid"])
    assert second.b2_uuid == uuid.UUID(files[1]["b2_uuid"])
    assert second.hide is True
    assert first.media_path._path.startswith("b2://archive/tv/")


@pytest.mark.django_db
def test_movie_publish_creates_one_mediafile_and_publishes_parent(
    client, create_user, create_movie, settings
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "movies/"
    movie = create_movie()
    parent = movie.mediapath_set.get()
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    object_id = str(uuid.uuid4())
    payload = {
        "pk": None,
        "filename": "Film.2025.mkv",
        "b2_uuid": object_id,
        "size": 30,
        "subtitle_files": [],
    }
    url = reverse("mediaviewer:api:migrations-publish", args=[parent.pk])
    response = client.post(
        url,
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": [payload]},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    parent.refresh_from_db()
    created = MediaFile.objects.get(media_path=parent)
    assert parent.filename == payload["filename"]
    assert str(created.b2_uuid) == object_id
    assert created.size == 30
    assert parent._path.startswith("b2://archive/movies/")


@pytest.mark.django_db
def test_movie_with_existing_child_and_unset_parent_filename_publishes(
    client, create_user, create_movie, settings
):
    settings.B2_BUCKET_NAME = "archive"
    movie = create_movie()
    parent = movie.mediapath_set.get()
    child = MediaFile.objects.create(
        media_path=parent, filename="Existing.mkv", display_name="original title"
    )
    parent.filename = None
    parent.save(update_fields=("filename",))
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    child_manifest = {
        "pk": child.pk,
        "filename": child.filename,
        "b2_uuid": str(uuid.uuid4()),
        "size": 10,
        "subtitle_files": [],
    }
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[parent.pk]),
        {
            "run_id": run_id,
            "snapshot": candidate["snapshot"],
            "files": [child_manifest],
        },
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    child.refresh_from_db()
    assert child.display_name == "original title"


@pytest.mark.django_db
def test_new_movie_child_must_match_existing_parent_filename(
    client, create_user, create_movie, settings
):
    settings.B2_BUCKET_NAME = "archive"
    movie = create_movie()
    parent = movie.mediapath_set.get()
    parent.filename = "Expected.mkv"
    parent.save(update_fields=("filename",))
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    manifest = {
        "pk": None,
        "filename": "Other.mkv",
        "b2_uuid": str(uuid.uuid4()),
        "size": 10,
        "subtitle_files": [],
    }
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[parent.pk]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": [manifest]},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not MediaFile.objects.filter(media_path=parent).exists()


@pytest.mark.django_db
def test_invalid_manifest_does_not_publish(
    client, create_user, create_tv_media_file, settings
):
    settings.B2_BUCKET_NAME = "archive"
    settings.B2_NAME_PREFIX = "tv/"
    media_file = create_tv_media_file(filename="Show.S01E01.mp4")
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    payload = {
        "pk": media_file.pk,
        "filename": "../escape.mp4",
        "b2_uuid": str(uuid.uuid4()),
        "size": 1,
        "subtitle_files": [],
    }
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[media_file.media_path_id]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": [payload]},
        content_type="application/json",
    )
    assert response.status_code == 400
    media_file.refresh_from_db()
    assert media_file.b2_uuid is None
    assert not MediaPath.objects.get(pk=media_file.media_path_id)._path.startswith(
        "b2://"
    )


@pytest.mark.django_db
def test_publish_rolls_back_prior_child_when_later_save_fails(
    client, create_user, create_tv_media_file, settings, mocker
):
    settings.B2_BUCKET_NAME = "archive"
    first = create_tv_media_file(filename="Show.S01E01.mp4")
    second = MediaFile.objects.create(
        media_path=first.media_path, filename="Show.S01E02.mp4", display_name="second"
    )
    owner = create_user(is_staff=True)
    client.force_login(owner)
    run_id = str(uuid.uuid4())
    client.post(
        reverse("mediaviewer:api:migrations-run"),
        {"run_id": run_id, "writers_paused": True},
        content_type="application/json",
    )
    candidate = client.get(
        reverse("mediaviewer:api:migrations-candidates"), {"limit": 10}
    ).json()["candidates"][0]
    files = [
        {
            "pk": first.pk,
            "filename": first.filename,
            "b2_uuid": str(uuid.uuid4()),
            "size": 1,
            "subtitle_files": [],
        },
        {
            "pk": second.pk,
            "filename": second.filename,
            "b2_uuid": str(uuid.uuid4()),
            "size": 2,
            "subtitle_files": [],
        },
    ]
    original_save = MediaFile.save
    calls = 0

    def fail_second_save(instance, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            from django.db import IntegrityError

            raise IntegrityError("simulated failure")
        return original_save(instance, *args, **kwargs)

    mocker.patch.object(MediaFile, "save", fail_second_save)
    response = client.post(
        reverse("mediaviewer:api:migrations-publish", args=[first.media_path_id]),
        {"run_id": run_id, "snapshot": candidate["snapshot"], "files": files},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not MediaFile.objects.filter(
        pk__in=(first.pk, second.pk), b2_uuid__isnull=False
    ).exists()
    assert not MediaPath.objects.get(pk=first.media_path_id).is_b2
