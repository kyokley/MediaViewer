import hashlib
import uuid
from unittest.mock import call

import pytest
import requests
from django.test import Client
from django.urls import reverse

from mediaviewer.b2 import B2Error
from mediaviewer.models import DownloadToken, MediaFile, VideoProgress


def _set_b2(media_path, key, filename=None, subtitles=None):
    media_path._path = f"b2://bucket/{key}"
    media_path.filename = filename
    media_path.subtitle_files = subtitles or []
    media_path.save()


@pytest.mark.django_db
@pytest.mark.parametrize("use_uuid", (True, False))
@pytest.mark.parametrize("is_movie", (True, False))
def test_b2_player_defers_signed_media_and_subtitles(
    mocker,
    client,
    create_user,
    create_movie,
    create_tv_media_file,
    use_uuid,
    is_movie,
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    if is_movie:
        obj = create_movie()
        media_path = obj.media_path
        filename = "The.Movie.mkv"
    else:
        obj = create_tv_media_file(filename="Episode.mkv")
        media_path = obj.media_path
        filename = obj.filename
    subtitle_name = "subtitle.vtt"
    _set_b2(
        media_path,
        f"archive/{media_path.pk}/",
        filename,
        [subtitle_name] if is_movie and not use_uuid else None,
    )
    if use_uuid:
        if is_movie:
            MediaFile.objects.create(
                media_path=media_path,
                filename=filename,
                b2_uuid=uuid.uuid4(),
                subtitle_files=[subtitle_name],
            )
        else:
            obj.b2_uuid = uuid.uuid4()
            obj.subtitle_files = [subtitle_name]
            obj.save()
    elif not is_movie:
        obj.subtitle_files = [subtitle_name]
        obj.save()

    get_b2_client = mocker.patch("mediaviewer.b2.get_b2_client")
    b2_client = get_b2_client.return_value
    b2_client.generate_presigned_url.side_effect = lambda bucket, key, expires_in: (
        f"https://signed.example/{key}"
    )
    token = (
        DownloadToken.objects.from_movie(user, obj)
        if is_movie
        else DownloadToken.objects.from_media_file(user, obj)
    )
    client.force_login(user)

    response = client.get(reverse("mediaviewer:b2player", args=(token.guid,)))

    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    assert b2_client.generate_presigned_url.call_count == 0
    get_b2_client.assert_not_called()
    assert "https://signed.example/" not in response.content.decode()
    assert response.context["player_config"]["media_url"] == reverse(
        "mediaviewer:b2playermedia", args=(token.guid,)
    )
    assert response.context["player_config"]["captions_enabled"] is False
    assert response.context["player_config"]["captions_url"] == reverse(
        "mediaviewer:b2playercaptions", args=(token.guid,)
    )
    assert "source_url" not in response.context["player_config"]
    assert "subtitle_urls" not in response.context["player_config"]
    b2_prefix = f"archive/{media_path.pk}/"
    if use_uuid:
        padded_id = f"{media_path.pk:09d}"
        segments = "/".join(padded_id[index : index + 3] for index in range(0, 9, 3))
        b2_prefix = f"archive/{segments}/"
    if use_uuid:
        uuid_file = (
            obj
            if not is_movie
            else MediaFile.objects.get(media_path=media_path, b2_uuid__isnull=False)
        )
        expected_source = f"{b2_prefix}{uuid_file.b2_uuid}.mkv"
    else:
        expected_source = f"{b2_prefix}{filename}"
    expected_subtitle = f"{b2_prefix}{subtitle_name}"
    media_response = client.get(
        reverse("mediaviewer:b2playermedia", args=(token.guid,))
    )
    assert media_response.status_code == 200
    assert media_response["Cache-Control"] == "private, no-store"
    assert media_response["Referrer-Policy"] == "no-referrer"
    assert set(media_response.json()) == {"source_url", "subtitle_urls"}
    assert media_response.json() == {
        "source_url": f"https://signed.example/{expected_source}",
        "subtitle_urls": [f"https://signed.example/{expected_subtitle}"],
    }
    assert b2_client.generate_presigned_url.call_args_list == [
        call(bucket="bucket", key=expected_source, expires_in=None),
        call(bucket="bucket", key=expected_subtitle, expires_in=None),
    ]
    media_identity = f"mediafile:{obj.pk}" if not is_movie else f"movie:{obj.pk}"
    expected_progress_hash = hashlib.sha256(
        f"b2:{media_path.pk}:{media_identity}:{filename}".encode("utf-8")
    ).hexdigest()
    expected_progress_url = reverse(
        "mediaviewer:ajaxvideoprogress",
        kwargs={"guid": token.guid, "hashed_filename": expected_progress_hash},
    )
    assert response.context["player_config"]["progress_url"] == expected_progress_url


@pytest.mark.django_db
def test_b2_player_media_denies_invalid_requests_before_presigning(
    client, create_user, create_tv_media_file, mocker
):
    from datetime import timedelta

    from django.utils import timezone

    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    other_user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    valid_token = DownloadToken.objects.from_media_file(user, media_file)
    expired_token = DownloadToken.objects.from_media_file(user, media_file)
    expired_token.date_created = timezone.now() - timedelta(days=1)
    expired_token.save(update_fields=("date_created",))
    local_file = create_tv_media_file()
    local_token = DownloadToken.objects.from_media_file(user, local_file)
    presign = mocker.patch("mediaviewer.b2.get_b2_client")

    def media_url(guid):
        return reverse("mediaviewer:b2playermedia", args=(guid,))

    anonymous_response = client.get(media_url(valid_token.guid))
    client.force_login(other_user)
    owner_response = client.get(media_url(valid_token.guid))
    client.force_login(user)
    expired_response = client.get(media_url(expired_token.guid))
    unknown_response = client.get(media_url("missing"))
    local_response = client.get(media_url(local_token.guid))
    user_settings = user.settings()
    user_settings.can_download = False
    user_settings.save()
    capability_response = client.get(media_url(valid_token.guid))

    assert anonymous_response.status_code == 302
    assert owner_response.status_code == 404
    assert expired_response.status_code == 404
    assert unknown_response.status_code == 404
    assert local_response.status_code == 404
    assert capability_response.status_code == 403
    presign.assert_not_called()


@pytest.mark.django_db
def test_b2_player_media_rejects_incomplete_source_before_presigning(
    client, create_user, create_movie, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    movie = create_movie()
    _set_b2(movie.media_path, "archive/Movie/")
    token = DownloadToken.objects.from_movie(user, movie)
    presign = mocker.patch("mediaviewer.b2.get_b2_client")
    client.force_login(user)

    response = client.get(reverse("mediaviewer:b2playermedia", args=(token.guid,)))

    assert response.status_code == 404
    presign.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "error", (B2Error("B2 authorization failed"), requests.ConnectionError("offline"))
)
def test_b2_player_media_sanitizes_presign_errors(
    client, create_user, create_tv_media_file, mocker, error
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    client.force_login(user)
    mocker.patch(
        "mediaviewer.b2.get_b2_client"
    ).return_value.generate_presigned_url.side_effect = error

    response = client.get(reverse("mediaviewer:b2playermedia", args=(token.guid,)))

    assert response.status_code == 502
    assert response.content == b"Media URL generation failed"
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    assert str(error).encode() not in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("error", (ValueError, TypeError, AttributeError))
def test_b2_player_media_preserves_invalid_media_404(
    client, create_user, create_tv_media_file, mocker, error
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    client.force_login(user)
    mocker.patch.object(
        type(media_file), "downloadLink", side_effect=error("invalid media")
    )

    response = client.get(reverse("mediaviewer:b2playermedia", args=(token.guid,)))

    assert response.status_code == 404
    assert b"invalid media" not in response.content


@pytest.mark.django_db
def test_b2_player_media_rejects_non_get_without_presigning(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    client.force_login(user)
    get_b2_client = mocker.patch("mediaviewer.b2.get_b2_client")

    response = client.post(reverse("mediaviewer:b2playermedia", args=(token.guid,)))

    assert response.status_code == 405
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    get_b2_client.assert_not_called()


@pytest.mark.django_db
def test_b2_player_requires_login_and_token_owner(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    other_user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    url = reverse("mediaviewer:b2player", args=(token.guid,))

    anonymous_response = client.get(url)
    client.force_login(other_user)
    owner_mismatch_response = client.get(url)

    assert anonymous_response.status_code == 302
    assert owner_mismatch_response.status_code == 302
    assert owner_mismatch_response["Location"] == reverse("mediaviewer:notfound")
    assert owner_mismatch_response["Cache-Control"] == "private, no-store"
    assert owner_mismatch_response["Referrer-Policy"] == "no-referrer"


@pytest.mark.django_db
def test_b2_player_rejects_expired_unknown_and_local_tokens(
    client, create_user, create_tv_media_file, mocker
):
    from datetime import timedelta

    from django.utils import timezone

    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    b2_file = create_tv_media_file()
    _set_b2(b2_file.media_path, "archive/Show/", b2_file.filename)
    expired_token = DownloadToken.objects.from_media_file(user, b2_file)
    expired_token.date_created = timezone.now() - timedelta(days=1)
    expired_token.save(update_fields=("date_created",))
    local_file = create_tv_media_file()
    local_token = DownloadToken.objects.from_media_file(user, local_file)
    client.force_login(user)

    expired_response = client.get(
        reverse("mediaviewer:b2player", args=(expired_token.guid,))
    )
    unknown_response = client.get(reverse("mediaviewer:b2player", args=("missing",)))
    local_response = client.get(
        reverse("mediaviewer:b2player", args=(local_token.guid,))
    )

    not_found_url = reverse("mediaviewer:notfound")
    for response in (expired_response, unknown_response, local_response):
        assert response.status_code == 302
        assert response["Location"] == not_found_url
        assert response["Cache-Control"] == "private, no-store"
        assert response["Referrer-Policy"] == "no-referrer"


@pytest.mark.django_db
def test_b2_player_missing_page_redirects_to_public_themed_404(client, create_user):
    user = create_user()
    client.force_login(user)
    unknown_url = reverse("mediaviewer:b2player", args=("missing",))

    response = client.get(f"{unknown_url}?private=value")

    assert response.status_code == 302
    assert response["Location"] == reverse("mediaviewer:notfound")
    assert "missing" not in response["Location"]
    assert "private" not in response["Location"]
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    followed_response = client.get(f"{unknown_url}?private=value", follow=True)
    assert followed_response.status_code == 404
    assert followed_response.redirect_chain == [(reverse("mediaviewer:notfound"), 302)]
    assert followed_response.context["title"] == "Page not found"
    assert "Page not found" in followed_response.content.decode()
    assert followed_response["Cache-Control"] == "private, no-store"
    assert followed_response["Referrer-Policy"] == "no-referrer"


@pytest.mark.django_db
@pytest.mark.parametrize("theme", ("light", "dark"))
def test_notfound_is_public_and_uses_session_theme(client, theme):
    session = client.session
    session["theme"] = theme
    session.save()

    response = client.get(reverse("mediaviewer:notfound"))

    assert response.status_code == 404
    assert response.context["title"] == "Page not found"
    assert response.context["theme"] == theme
    assert response.context["loggedin"] is False
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"


@pytest.mark.django_db
def test_b2_player_checks_capability_before_presigning(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    user_settings = user.settings()
    user_settings.can_download = False
    user_settings.save()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    presign = mocker.patch("mediaviewer.b2.get_b2_client")
    client.force_login(user)

    response = client.get(reverse("mediaviewer:b2player", args=(token.guid,)))

    assert response.status_code == 403
    presign.assert_not_called()


@pytest.mark.django_db
def test_b2_ajax_button_checks_permission_before_token_or_presign(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    user_settings = user.settings()
    user_settings.can_download = False
    user_settings.save()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    presign = mocker.patch("mediaviewer.b2.get_b2_client")
    client.force_login(user)

    response = client.post(
        reverse("mediaviewer:ajaxdownloadbutton"), {"mf_id": media_file.pk}
    )

    assert response.status_code == 403
    assert not DownloadToken.objects.filter(user=user).exists()
    presign.assert_not_called()


@pytest.mark.django_db
def test_b2_ajax_button_returns_player_route_and_local_stays_waiter(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    client.force_login(user)

    b2_response = client.post(
        reverse("mediaviewer:ajaxdownloadbutton"), {"mf_id": media_file.pk}
    )
    b2_data = b2_response.json()
    assert b2_data["downloadLink"] == reverse(
        "mediaviewer:b2player", args=(b2_data["guid"],)
    )

    local_file = create_tv_media_file()
    local_response = client.post(
        reverse("mediaviewer:ajaxdownloadbutton"), {"mf_id": local_file.pk}
    )
    assert "waiter" in local_response.json()["downloadLink"]


@pytest.mark.django_db
def test_b2_movie_ajax_button_returns_player_route(
    client, create_user, create_movie, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    movie = create_movie()
    media_path = movie.media_path
    _set_b2(media_path, f"archive/{media_path.pk}/", "Movie.mkv")
    client.force_login(user)

    response = client.post(
        reverse("mediaviewer:ajaxdownloadbutton"), {"movie_id": movie.pk}
    )

    data = response.json()
    assert response.status_code == 200
    assert data["downloadLink"] == reverse("mediaviewer:b2player", args=(data["guid"],))


@pytest.mark.django_db
def test_b2_player_rejects_incomplete_movie_without_presigning(
    client, create_user, create_movie, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    movie = create_movie()
    media_path = movie.media_path
    _set_b2(media_path, "archive/Movie/")
    token = DownloadToken.objects.from_movie(user, movie)
    presign = mocker.patch("mediaviewer.b2.get_b2_client")
    client.force_login(user)

    response = client.get(reverse("mediaviewer:b2player", args=(token.guid,)))

    assert response.status_code == 302
    assert response["Location"] == reverse("mediaviewer:notfound")
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    presign.assert_not_called()


@pytest.mark.django_db
def test_b2_player_deleted_media_redirects_to_themed_404(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    guid = token.guid
    media_file.delete()
    client.force_login(user)

    response = client.get(reverse("mediaviewer:b2player", args=(guid,)))

    assert response.status_code == 302
    assert response["Location"] == reverse("mediaviewer:notfound")
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    assert not DownloadToken.objects.filter(guid=guid).exists()


@pytest.mark.django_db
def test_b2_ajax_button_rejects_incomplete_movie_without_minting_token_or_presigning(
    client, create_user, create_movie, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    movie = create_movie()
    media_path = movie.media_path
    _set_b2(media_path, "archive/Movie/")
    presign = mocker.patch("mediaviewer.b2.get_b2_client")
    client.force_login(user)

    response = client.post(
        reverse("mediaviewer:ajaxdownloadbutton"), {"movie_id": movie.pk}
    )

    assert response.status_code == 404
    assert not DownloadToken.objects.filter(user=user).exists()
    presign.assert_not_called()


@pytest.mark.django_db
def test_b2_player_reuses_persisted_progress_across_refreshed_tokens(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file(filename="Episode.mkv")
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    VideoProgress.objects.create(
        user=user,
        media_file=media_file,
        filename=media_file.filename,
        hashed_filename="progress-original-hash",
        offset=42,
    )
    b2_client = mocker.patch("mediaviewer.b2.get_b2_client").return_value
    b2_client.generate_presigned_url.return_value = "https://signed.example/video"
    client.force_login(user)

    first_token = DownloadToken.objects.from_media_file(user, media_file)
    first_response = client.get(
        reverse("mediaviewer:b2player", args=(first_token.guid,))
    )
    refreshed_token = DownloadToken.objects.from_media_file(user, media_file)
    refreshed_response = client.get(
        reverse("mediaviewer:b2player", args=(refreshed_token.guid,))
    )

    expected_hash = "progress-original-hash"
    assert first_response.context["player_config"]["progress_url"] == reverse(
        "mediaviewer:ajaxvideoprogress",
        kwargs={"guid": first_token.guid, "hashed_filename": expected_hash},
    )
    assert refreshed_response.context["player_config"]["progress_url"] == reverse(
        "mediaviewer:ajaxvideoprogress",
        kwargs={"guid": refreshed_token.guid, "hashed_filename": expected_hash},
    )


@pytest.mark.django_db
def test_movie_backed_mediafile_uses_movie_detail_route_and_movie_context(
    client, create_user, create_movie_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_movie_media_file(filename="Movie.mkv")
    media_path = media_file.media_path
    _set_b2(media_path, f"archive/{media_path.pk}/", media_file.filename)
    b2_client = mocker.patch("mediaviewer.b2.get_b2_client").return_value
    b2_client.generate_presigned_url.return_value = "https://signed.example/video"
    token = DownloadToken.objects.from_media_file(user, media_file)
    client.force_login(user)

    response = client.get(reverse("mediaviewer:b2player", args=(token.guid,)))

    assert response.status_code == 200
    assert response.context["is_movie"] is True
    assert response.context["details_url"] == reverse(
        "mediaviewer:moviedetail", args=(media_file.movie.pk,)
    )
    assert response.context["previous_url"] is None
    assert response.context["next_url"] is None


@pytest.mark.django_db
def test_b2_autoplay_uses_internal_player_but_local_keeps_waiter(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    b2_file = create_tv_media_file()
    _set_b2(b2_file.media_path, "archive/Show/", b2_file.filename)
    local_file = create_tv_media_file()
    client.force_login(user)

    b2_response = client.get(
        reverse("mediaviewer:autoplaydownloadlink", args=(b2_file.pk,))
    )
    local_response = client.get(
        reverse("mediaviewer:autoplaydownloadlink", args=(local_file.pk,))
    )

    token = DownloadToken.objects.get_by_guid(b2_response.url.rsplit("/", 2)[-2])
    assert token is not None
    assert b2_response.url == reverse("mediaviewer:b2player", args=(token.guid,))
    assert "waiter" in local_response.url


@pytest.mark.django_db
@pytest.mark.parametrize("is_movie", (True, False))
def test_b2_listing_open_does_not_depend_on_waiter_status(
    create_user,
    create_movie,
    create_tv_media_file,
    is_movie,
    mocker,
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    obj = create_movie() if is_movie else create_tv_media_file()
    media_path = obj.media_path
    _set_b2(media_path, "archive/", obj.name if is_movie else obj.filename)

    payload = obj.ajax_row_payload(can_download=True, waiterstatus=False, user=user)

    assert "Open" in payload[2]


@pytest.mark.django_db
@pytest.mark.parametrize("is_movie", (True, False))
def test_local_listing_open_still_requires_waiter_status(
    create_user, create_movie, create_tv_media_file, is_movie, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    obj = create_movie() if is_movie else create_tv_media_file()

    payload = obj.ajax_row_payload(can_download=True, waiterstatus=False, user=user)

    assert payload[2] == "Alfred is down"


@pytest.mark.django_db
@pytest.mark.parametrize(("value", "expected"), (("true", True), ("false", False)))
def test_b2_player_captions_preference_updates_only_current_user(
    client, create_user, create_tv_media_file, mocker, value, expected
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    other_user = create_user()
    user_settings = user.settings()
    user_settings.captions_enabled = not expected
    user_settings.save(update_fields=("captions_enabled",))
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    client.force_login(user)

    response = client.post(
        reverse("mediaviewer:b2playercaptions", args=(token.guid,)),
        {"captions_enabled": value},
    )

    assert response.status_code == 204
    assert response["Cache-Control"] == "private, no-store"
    assert response["Referrer-Policy"] == "no-referrer"
    user.settings().refresh_from_db()
    other_user.settings().refresh_from_db()
    assert user.settings().captions_enabled is expected
    assert other_user.settings().captions_enabled is False

    player_response = client.get(reverse("mediaviewer:b2player", args=(token.guid,)))
    assert player_response.status_code == 200
    assert player_response.context["player_config"]["captions_enabled"] is expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload", ({}, {"captions_enabled": "TRUE"}, {"captions_enabled": "1"})
)
def test_b2_player_captions_rejects_invalid_payload_without_writes(
    client, create_user, create_tv_media_file, mocker, payload
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    initial_dateedited = user.settings().dateedited
    client.force_login(user)

    response = client.post(
        reverse("mediaviewer:b2playercaptions", args=(token.guid,)), payload
    )

    assert response.status_code == 400
    user.settings().refresh_from_db()
    assert user.settings().captions_enabled is False
    assert user.settings().dateedited == initial_dateedited


@pytest.mark.django_db
def test_b2_player_captions_requires_owner_login_and_post(
    client, create_user, create_tv_media_file, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    other_user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    url = reverse("mediaviewer:b2playercaptions", args=(token.guid,))

    anonymous_response = client.post(url, {"captions_enabled": "true"})
    client.force_login(other_user)
    owner_mismatch_response = client.post(url, {"captions_enabled": "true"})
    client.force_login(user)
    wrong_method_response = client.get(url)

    assert anonymous_response.status_code == 302
    assert owner_mismatch_response.status_code == 404
    assert wrong_method_response.status_code == 405
    user.settings().refresh_from_db()
    assert user.settings().captions_enabled is False


@pytest.mark.django_db
def test_b2_player_captions_requires_csrf(create_user, create_tv_media_file, mocker):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    media_file = create_tv_media_file()
    _set_b2(media_file.media_path, "archive/Show/", media_file.filename)
    token = DownloadToken.objects.from_media_file(user, media_file)
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(user)

    response = csrf_client.post(
        reverse("mediaviewer:b2playercaptions", args=(token.guid,)),
        {"captions_enabled": "true"},
    )

    assert response.status_code == 403
    user.settings().refresh_from_db()
    assert user.settings().captions_enabled is False


@pytest.mark.django_db
@pytest.mark.parametrize("can_download", (True, False))
@pytest.mark.parametrize("is_movie", (True, False))
def test_b2_detail_context_supports_player_gate_without_waiter(
    client,
    create_user,
    create_movie,
    create_tv_media_file,
    can_download,
    is_movie,
    mocker,
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user = create_user()
    user_settings = user.settings()
    user_settings.can_download = can_download
    user_settings.save()
    if is_movie:
        obj = create_movie()
        media_path = obj.media_path
        _set_b2(media_path, f"archive/{media_path.pk}/", "Movie.mkv")
        url = reverse("mediaviewer:moviedetail", args=(obj.pk,))
    else:
        obj = create_tv_media_file()
        _set_b2(obj.media_path, "archive/Show/", obj.filename)
        url = reverse("mediaviewer:tvdetail", args=(obj.pk,))
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 200
    assert response.context["is_b2"] is True
    assert response.context["can_download"] is can_download
