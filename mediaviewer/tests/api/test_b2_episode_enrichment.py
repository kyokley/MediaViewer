import uuid
from datetime import date
from types import SimpleNamespace

import pytest
import requests
from django.db import transaction
from django.urls import reverse

from mediaviewer.models import MediaFile, Poster
from mediaviewer.models.tvdbconfiguration import tvdbConfig


def _mock_successful_metadata(mocker, settings):
    settings.API_KEY = "fixture-api-key"
    mocker.patch.object(tvdbConfig, "connected", True)
    mocker.patch.object(tvdbConfig, "url", "https://images.example.test")
    mocker.patch.object(tvdbConfig, "poster_size", "original/")

    series_data = {
        "id": 4242,
        "name": "Original Show",
        "overview": "Series overview",
        "poster_path": "/series-poster.jpg",
        "genres": [],
    }
    episode_data = {
        "id": 424202,
        "name": "Pilot",
        "overview": "Episode overview",
        "still_path": "/episode-still.jpg",
        "air_date": "2024-01-02",
    }
    cast_data = {"cast": [], "crew": []}
    extended_data = {
        "imdb_id": "tt004242",
        "vote_average": 8.4,
        "tagline": "A fixture tagline",
    }
    json_responses = {
        "/tv/4242?language=en-US&api_key=fixture-api-key": series_data,
        "/tv/4242/season/1/episode/2/credits?api_key=fixture-api-key": cast_data,
        "/tv/4242/external_ids?api_key=fixture-api-key": extended_data,
        "/tv/4242/season/1/episode/2?api_key=fixture-api-key": episode_data,
    }

    def json_response(url):
        for endpoint, payload in json_responses.items():
            if endpoint in url:
                return payload
        raise AssertionError(f"Unexpected TMDB request: {url}")

    get_json = mocker.patch(
        "mediaviewer.models.poster.getJSONData", side_effect=json_response
    )
    tvdb_get_json = mocker.patch(
        "mediaviewer.models.tvdbconfiguration.getJSONData", side_effect=json_response
    )
    image_response = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        iter_content=lambda chunk_size: [b"fixture-image"],
    )
    image_get = mocker.patch(
        "mediaviewer.models.poster.requests.get", return_value=image_response
    )
    return get_json, tvdb_get_json, image_get


@pytest.mark.django_db
def test_uuid_tv_upload_enriches_episode_metadata_immediately(
    client, create_user, create_tv, mocker, settings, django_capture_on_commit_callbacks
):
    user = create_user(is_staff=True)
    client.force_login(user)
    tv = create_tv(name="Original Show")
    media_path = tv.media_path
    media_path._path = f"b2://episode-fixtures/tv/{media_path.pk}/"
    media_path.save(update_fields=("_path",))

    series_poster = Poster.objects.create(tmdb="4242")
    tv._poster = series_poster
    tv.save(update_fields=("_poster",))

    get_json, tvdb_get_json, image_get = _mock_successful_metadata(mocker, settings)

    object_uuid = uuid.uuid4()
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = client.post(
            reverse("mediaviewer:api:mediafile-list"),
            data={
                "filename": "Original.Show.S01E02.mv-encoded.mp4",
                "media_path": media_path.pk,
                "b2_uuid": str(object_uuid),
            },
            format="json",
        )

    assert response.status_code == 201, response.json()
    assert len(callbacks) == 1
    media_file = MediaFile.objects.get(pk=response.json()["pk"])
    poster = Poster.objects.get(pk=media_file._poster_id)
    assert media_file.filename == "Original.Show.S01E02.mv-encoded.mp4"
    assert media_file.b2_uuid == object_uuid
    assert (media_file.season, media_file.episode) == (1, 2)
    assert poster.episodename == "Pilot"
    assert poster.extendedplot == "Episode overview"
    assert poster.release_date == date(2024, 1, 2)
    assert media_file.display_name == "S01 E02: Pilot"

    episode_url = (
        "https://api.themoviedb.org/3/tv/4242/season/1/episode/2"
        "?api_key=fixture-api-key"
    )
    assert any(call.args[0] == episode_url for call in tvdb_get_json.call_args_list)
    assert any(
        "/episode/2/credits?" in call.args[0] for call in get_json.call_args_list
    )
    assert any("/external_ids?" in call.args[0] for call in get_json.call_args_list)
    image_get.assert_called_once_with(
        "https://images.example.test/episode-still.jpg",
        stream=True,
        timeout=settings.REQUEST_TIMEOUT,
    )


@pytest.mark.django_db(transaction=True)
def test_uuid_tv_upload_response_includes_enriched_display_name(
    client, create_user, create_tv, mocker, settings
):
    client.force_login(create_user(is_staff=True))
    tv = create_tv(name="Original Show")
    media_path = tv.media_path
    media_path._path = f"b2://episode-fixtures/tv/{media_path.pk}/"
    media_path.save(update_fields=("_path",))
    tv._poster = Poster.objects.create(tmdb="4242")
    tv.save(update_fields=("_poster",))
    _mock_successful_metadata(mocker, settings)

    response = client.post(
        reverse("mediaviewer:api:mediafile-list"),
        data={
            "filename": "Original.Show.S01E02.mv-encoded.mp4",
            "media_path": media_path.pk,
            "b2_uuid": str(uuid.uuid4()),
        },
        format="json",
    )

    assert response.status_code == 201, response.json()
    assert response.json()["display_name"] == "S01 E02: Pilot"


@pytest.mark.django_db
def test_uuid_tv_upload_succeeds_when_episode_metadata_requests_fail(
    client, create_user, create_tv, mocker, django_capture_on_commit_callbacks
):
    user = create_user(is_staff=True)
    client.force_login(user)
    tv = create_tv(name="Request Failure Show")
    media_path = tv.media_path
    media_path._path = f"b2://episode-fixtures/tv/{media_path.pk}/"
    media_path.save(update_fields=("_path",))
    series_poster = Poster.objects.create(tmdb="5252")
    tv._poster = series_poster
    tv.save(update_fields=("_poster",))

    mocker.patch.object(tvdbConfig, "connected", True)
    mocker.patch(
        "mediaviewer.models.poster.getJSONData",
        side_effect=requests.ConnectionError("fixture request failure"),
    )
    get_json = mocker.patch(
        "mediaviewer.models.tvdbconfiguration.getJSONData",
        side_effect=requests.ConnectionError("fixture request failure"),
    )
    mocker.patch(
        "mediaviewer.models.poster.requests.get",
        side_effect=requests.ConnectionError("fixture image failure"),
    )

    object_uuid = uuid.uuid4()
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = client.post(
            reverse("mediaviewer:api:mediafile-list"),
            data={
                "filename": "Request.Failure.Show.S01E02.mkv",
                "media_path": media_path.pk,
                "b2_uuid": str(object_uuid),
            },
            format="json",
        )

    assert response.status_code == 201, response.json()
    assert len(callbacks) == 1
    media_file = MediaFile.objects.get(pk=response.json()["pk"])
    assert media_file.b2_uuid == object_uuid
    assert media_file.filename == "Request.Failure.Show.S01E02.mkv"
    assert (media_file.season, media_file.episode) == (1, 2)
    assert media_file._poster_id
    assert get_json.called

    with django_capture_on_commit_callbacks(execute=True) as replay_callbacks:
        replay = client.post(
            reverse("mediaviewer:api:mediafile-list"),
            data={
                "filename": media_file.filename,
                "media_path": media_file.media_path_id,
                "b2_uuid": str(object_uuid),
            },
            format="json",
        )

    assert replay.status_code == 201
    assert replay.json()["pk"] == media_file.pk
    assert replay_callbacks == []


@pytest.mark.django_db
def test_movie_and_unparseable_uploads_do_not_schedule_enrichment(
    client, create_user, create_tv, create_movie, django_capture_on_commit_callbacks
):
    client.force_login(create_user(is_staff=True))
    tv = create_tv()
    movie = create_movie()
    url = reverse("mediaviewer:api:mediafile-list")

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        movie_response = client.post(
            url,
            {
                "filename": "A.Movie.mkv",
                "media_path": movie.media_path.pk,
                "b2_uuid": str(uuid.uuid4()),
            },
            format="json",
        )
        tv_response = client.post(
            url,
            {
                "filename": "unparseable-file.mkv",
                "media_path": tv.media_path.pk,
                "b2_uuid": str(uuid.uuid4()),
            },
            format="json",
        )

    assert movie_response.status_code == 201, movie_response.json()
    assert tv_response.status_code == 201, tv_response.json()
    assert callbacks == []


@pytest.mark.django_db
def test_exact_uuid_replay_does_not_schedule_a_second_enrichment(
    client, create_user, create_tv, django_capture_on_commit_callbacks
):
    client.force_login(create_user(is_staff=True))
    tv = create_tv()
    payload = {
        "filename": "Replay.Show.S01E02.mkv",
        "media_path": tv.media_path.pk,
        "b2_uuid": str(uuid.uuid4()),
    }
    url = reverse("mediaviewer:api:mediafile-list")

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        created = client.post(url, payload, format="json")
        replay = client.post(url, payload, format="json")

    assert created.status_code == replay.status_code == 201
    assert replay.json()["pk"] == created.json()["pk"]
    assert len(callbacks) == 1


@pytest.mark.django_db
def test_uuid_conflict_does_not_schedule_enrichment(
    client, create_user, create_tv, django_capture_on_commit_callbacks
):
    client.force_login(create_user(is_staff=True))
    first_tv = create_tv()
    second_tv = create_tv()
    payload = {
        "filename": "Conflict.Show.S01E02.mkv",
        "media_path": first_tv.media_path.pk,
        "b2_uuid": str(uuid.uuid4()),
    }
    url = reverse("mediaviewer:api:mediafile-list")

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        created = client.post(url, payload, format="json")
        conflict = client.post(
            url,
            {**payload, "media_path": second_tv.media_path.pk},
            format="json",
        )

    assert created.status_code == 201
    assert conflict.status_code == 400
    assert len(callbacks) == 1


@pytest.mark.django_db(transaction=True)
def test_rolled_back_uuid_upload_discards_enrichment_callback(
    client, create_user, create_tv, django_capture_on_commit_callbacks
):
    client.force_login(create_user(is_staff=True))
    tv = create_tv()
    payload = {
        "filename": "Rollback.Show.S01E02.mkv",
        "media_path": tv.media_path.pk,
        "b2_uuid": str(uuid.uuid4()),
    }
    url = reverse("mediaviewer:api:mediafile-list")
    response = None

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        try:
            with transaction.atomic():
                response = client.post(url, payload, format="json")
                raise RuntimeError("force upload transaction rollback")
        except RuntimeError as error:
            assert str(error) == "force upload transaction rollback"

    assert response.status_code == 201
    assert callbacks == []
    assert not MediaFile.objects.filter(b2_uuid=payload["b2_uuid"]).exists()
