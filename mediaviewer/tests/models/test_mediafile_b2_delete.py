from pathlib import Path
from unittest.mock import Mock

import pytest
from django.db import transaction

from mediaviewer.models import MediaFile, MediaPath


def _use_b2(media_file):
    media_path = media_file.media_path
    media_path._path = f"b2://test-bucket/library/{media_path.pk}/{media_file.filename}"
    media_path.subtitle_files = ["movie-shared.vtt"]
    media_path.save(update_fields=("_path", "subtitle_files"))
    media_file.refresh_from_db()
    return media_path


def _mock_client(mocker):
    client = Mock()
    mocker.patch("mediaviewer.b2.get_b2_client", return_value=client)
    return client


@pytest.mark.django_db(transaction=True)
def test_instance_delete_removes_uuid_media_and_subtitle_keys(
    create_tv_media_file, mocker
):
    client = _mock_client(mocker)
    media_file = create_tv_media_file(filename="episode.mkv")
    media_file.b2_uuid = "00000000-0000-0000-0000-000000000001"
    media_file.subtitle_files = ["episode-en.vtt", "episode-en.vtt", "episode-es.vtt"]
    media_file.save(update_fields=("b2_uuid", "subtitle_files"))
    media_path = _use_b2(media_file)
    media_file_id = media_file.pk
    prefix = media_path.b2_upload_prefix

    media_file.delete()

    client.delete_file.assert_has_calls(
        [
            mocker.call(
                bucket="test-bucket",
                key=f"{prefix}{media_file.b2_uuid}{Path(media_file.filename).suffix}",
            ),
            mocker.call(bucket="test-bucket", key=f"{prefix}episode-en.vtt"),
            mocker.call(bucket="test-bucket", key=f"{prefix}episode-es.vtt"),
        ],
        any_order=False,
    )
    assert client.delete_file.call_count == 3
    assert not MediaFile.objects.filter(pk=media_file_id).exists()


@pytest.mark.django_db(transaction=True)
def test_queryset_delete_removes_legacy_file_and_subtitles(
    create_tv_media_file, mocker
):
    client = _mock_client(mocker)
    media_file = create_tv_media_file(filename="legacy episode.mkv")
    media_file.subtitle_files = ["legacy-en.vtt"]
    media_file.save(update_fields=("subtitle_files",))
    media_path = _use_b2(media_file)

    MediaFile.objects.filter(pk=media_file.pk).delete()

    assert [call.kwargs for call in client.delete_file.call_args_list] == [
        {"bucket": "test-bucket", "key": media_path.file_key(media_file.filename)},
        {"bucket": "test-bucket", "key": media_path.file_key("legacy-en.vtt")},
    ]


@pytest.mark.django_db(transaction=True)
def test_media_path_cascade_delete_captures_b2_data_before_parent_is_deleted(
    create_tv_media_file, mocker
):
    client = _mock_client(mocker)
    media_file = create_tv_media_file(filename="cascade.mkv")
    media_file.subtitle_files = ["cascade.vtt"]
    media_file.save(update_fields=("subtitle_files",))
    media_path = _use_b2(media_file)
    file_key = media_path.file_key(media_file.filename)
    subtitle_key = media_path.file_key("cascade.vtt")
    media_path_id = media_path.pk

    MediaPath.objects.get(pk=media_path_id).delete()

    assert [call.kwargs["key"] for call in client.delete_file.call_args_list] == [
        file_key,
        subtitle_key,
    ]


@pytest.mark.django_db(transaction=True)
def test_remote_deletion_waits_for_commit_and_is_skipped_on_rollback(
    create_tv_media_file, mocker
):
    client = _mock_client(mocker)
    media_file = create_tv_media_file(filename="transaction.mkv")
    _use_b2(media_file)

    with transaction.atomic():
        media_file.delete()
        client.delete_file.assert_not_called()

    client.delete_file.assert_called_once()

    another_file = create_tv_media_file(filename="rollback.mkv")
    _use_b2(another_file)
    another_file_id = another_file.pk
    client.delete_file.reset_mock()

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            another_file.delete()
            raise RuntimeError("rollback")

    client.delete_file.assert_not_called()
    assert MediaFile.objects.filter(pk=another_file_id).exists()


@pytest.mark.django_db(transaction=True)
def test_local_media_file_delete_does_not_create_b2_client(
    create_tv_media_file, mocker
):
    get_client = mocker.patch("mediaviewer.b2.get_b2_client")
    media_file = create_tv_media_file(filename="local.mkv")

    media_file.delete()

    get_client.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_file_delete_never_deletes_shared_movie_subtitles(
    create_movie_media_file, mocker
):
    client = _mock_client(mocker)
    media_file = create_movie_media_file(filename="movie.mkv")
    media_path = _use_b2(media_file)
    shared_subtitle_key = media_path.file_key("movie-shared.vtt")

    media_file.delete()

    deleted_keys = [call.kwargs["key"] for call in client.delete_file.call_args_list]
    assert deleted_keys == [media_path.file_key(media_file.filename)]
    assert shared_subtitle_key not in deleted_keys


@pytest.mark.django_db(transaction=True)
def test_delete_failure_logs_and_attempts_later_keys(create_tv_media_file, mocker):
    client = _mock_client(mocker)
    client.delete_file.side_effect = [RuntimeError("failed"), None, None]
    media_file = create_tv_media_file(filename="failure.mkv")
    media_file.subtitle_files = ["failure-a.vtt", "failure-b.vtt"]
    media_file.save(update_fields=("subtitle_files",))
    media_path = _use_b2(media_file)
    media_file_id = media_file.pk
    logger = mocker.patch("mediaviewer.models.mediafile.log")

    media_file.delete()

    assert client.delete_file.call_count == 3
    assert not MediaFile.objects.filter(pk=media_file_id).exists()
    logger.exception.assert_called_once()
    assert logger.exception.call_args.args[1:] == (
        "test-bucket",
        media_path.file_key(media_file.filename),
    )
