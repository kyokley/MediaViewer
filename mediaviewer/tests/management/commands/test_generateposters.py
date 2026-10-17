import uuid
from datetime import date

import pytest
from django.core.management import call_command

from mediaviewer.models import Poster


@pytest.mark.django_db
def test_selects_uuid_tv_episode_name_gap_but_excludes_other_records(
    create_tv_media_file, create_movie_media_file, mocker
):
    tv_file = create_tv_media_file(filename="show.mp4")
    tv_file.b2_uuid = uuid.uuid4()
    tv_file.season = 0
    tv_file.episode = 1
    tv_file.save()
    gap = Poster.objects.from_ref_obj(tv_file)
    gap.image = "uploads/existing.jpg"
    gap.release_date = date(2020, 1, 1)
    gap.save()

    ordinary_tv_file = create_tv_media_file(filename="ordinary.mp4")
    ordinary_tv_file.season = 1
    ordinary_tv_file.episode = 2
    ordinary_tv_file.save()
    ordinary = Poster.objects.from_ref_obj(ordinary_tv_file)
    ordinary.image = "uploads/existing.jpg"
    ordinary.release_date = date(2020, 1, 1)
    ordinary.save()

    zero_episode_file = create_tv_media_file(filename="zero-episode.mp4")
    zero_episode_file.b2_uuid = uuid.uuid4()
    zero_episode_file.season = 0
    zero_episode_file.episode = 0
    zero_episode_file.save()
    zero_episode = Poster.objects.from_ref_obj(zero_episode_file)
    zero_episode.image = "uploads/existing.jpg"
    zero_episode.release_date = date(2020, 1, 1)
    zero_episode.save()

    missing_coordinates_file = create_tv_media_file(filename="missing.mp4")
    missing_coordinates_file.b2_uuid = uuid.uuid4()
    missing_coordinates_file.save()
    missing_coordinates = Poster.objects.from_ref_obj(missing_coordinates_file)
    missing_coordinates.image = "uploads/existing.jpg"
    missing_coordinates.release_date = date(2020, 1, 1)
    missing_coordinates.save()

    movie_file = create_movie_media_file(filename="movie.mp4")
    movie_file.b2_uuid = uuid.uuid4()
    movie_file.season = 1
    movie_file.episode = 2
    movie_file.save()
    movie = Poster.objects.from_ref_obj(movie_file)
    movie.image = "uploads/existing.jpg"
    movie.release_date = date(2020, 1, 1)
    movie.save()

    selected = []
    populate = mocker.patch.object(
        Poster,
        "populate_data",
        autospec=True,
        side_effect=lambda poster: selected.append(poster.pk),
    )
    call_command("generateposters", limit="10", force=False)

    assert selected == [gap.pk]
    assert populate.call_count == 1


@pytest.mark.django_db
def test_name_gap_respects_limit_and_failure_does_not_stop_next(
    create_tv_media_file, mocker
):
    posters = []
    for index in range(2):
        media_file = create_tv_media_file(filename=f"show{index}.mp4")
        media_file.b2_uuid = uuid.uuid4()
        media_file.season = 1
        media_file.episode = index + 1
        media_file.save()
        poster = Poster.objects.from_ref_obj(media_file)
        poster.image = "uploads/existing.jpg"
        poster.release_date = date(2020, 1, 1)
        poster.save()
        posters.append(poster)

    populate = mocker.patch.object(Poster, "populate_data", autospec=True)
    populate.side_effect = [RuntimeError("failed metadata"), None]
    call_command("generateposters", limit="2", force=False)

    assert populate.call_count == 2
    assert {call.args[0].pk for call in populate.call_args_list} == {
        poster.pk for poster in posters
    }

    populate.reset_mock()
    populate.side_effect = None
    call_command("generateposters", limit="1", force=False)
    assert populate.call_count == 1
