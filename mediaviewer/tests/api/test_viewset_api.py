import json
import uuid
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from mediaviewer.models import MediaFile, MediaPath, Movie, TV
from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.django_db
@pytest.mark.parametrize("use_movie", (True, False))
@pytest.mark.parametrize("use_regular_user", (True, False))
class TestDownloadToken:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")

        self.user = create_user(is_staff=True)
        self.regular_user = create_user()

    def test_detail(
        self, client, use_movie, use_regular_user, create_movie, create_tv_media_file
    ):
        if use_regular_user:
            test_user = self.regular_user
        else:
            test_user = self.user
        client.force_login(test_user)

        if use_movie:
            movie = create_movie()
            dt = DownloadToken.objects.from_movie(test_user, movie)
        else:
            mf = create_tv_media_file()
            dt = DownloadToken.objects.from_media_file(test_user, mf)

        url = reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        response = client.get(url)
        if not use_regular_user:
            assert response.status_code == 200

            json_data = response.json()
            assert dt.guid == json_data["guid"]
            assert dt.user.username == json_data["username"]

            assert dt.ref_obj.full_name == json_data["displayname"]
            if not use_movie:
                assert json_data["original_filename"] == dt.media_file.filename
        else:
            assert response.status_code == 403

    def test_expired_token_has_no_download_link(
        self, client, use_movie, use_regular_user, create_movie, create_tv_media_file
    ):
        test_user = self.user
        client.force_login(test_user)

        if use_movie:
            movie = create_movie()
            dt = DownloadToken.objects.from_movie(test_user, movie)
        else:
            mf = create_tv_media_file()
            dt = DownloadToken.objects.from_media_file(test_user, mf)

        dt.date_created = dt.date_created - timezone.timedelta(
            hours=settings.TOKEN_VALIDITY_LENGTH
        )
        dt.save()

        url = reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()["download_link"] is None

    def test_local_token_has_no_subtitle_files(
        self, client, use_movie, use_regular_user, create_movie, create_tv_media_file
    ):
        test_user = self.user
        client.force_login(test_user)

        if use_movie:
            movie = create_movie()
            dt = DownloadToken.objects.from_movie(test_user, movie)
        else:
            mf = create_tv_media_file()
            dt = DownloadToken.objects.from_media_file(test_user, mf)

        url = reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()["subtitle_files"] == []


@pytest.mark.django_db
class TestDownloadTokenB2Subtitles:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.user = create_user(is_staff=True)
        self.mock_b2_client = mocker.patch("mediaviewer.b2.get_b2_client")
        self.mock_b2_client.return_value.generate_presigned_url.side_effect = (
            lambda bucket, key, expires_in: (
                f"https://b2.example.com/{bucket}/{key}?sig=abc"
            )
        )

    def test_b2_movie_token_has_subtitle_files(self, client, create_movie):
        client.force_login(self.user)
        movie = create_movie()
        mp = movie.mediapath_set.first()
        mp._path = "b2://mybucket/movies/Movie.Name/"
        mp.filename = "Movie.Name.mp4"
        mp.subtitle_files = [
            "Movie.Name.mp4.mv-encoded.mp4-0.vtt",
            "Movie.Name.mp4.mv-encoded.mp4-1.vtt",
        ]
        mp.save()

        dt = DownloadToken.objects.from_movie(self.user, movie)
        url = reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()["subtitle_files"] == [
            "https://b2.example.com/mybucket/movies/Movie.Name/Movie.Name.mp4.mv-encoded.mp4-0.vtt?sig=abc",
            "https://b2.example.com/mybucket/movies/Movie.Name/Movie.Name.mp4.mv-encoded.mp4-1.vtt?sig=abc",
        ]
        assert response.json()["original_filename"] == "Movie.Name.mp4"
        assert response.json()["download_link"].endswith(
            "movies/Movie.Name/Movie.Name.mp4?sig=abc"
        )

    def test_b2_tv_token_has_subtitle_files(self, client, create_tv_media_file):
        client.force_login(self.user)
        mf = create_tv_media_file(filename="Show.Name.S01E01.mv-encoded.mp4")
        mp = mf.media_path
        mp._path = "b2://mybucket/tv/Show.Name/"
        mp.save()
        mf.subtitle_files = ["Show.Name.S01E01.mv-encoded.mp4.mv-encoded.mp4-0.vtt"]
        mf.save()

        dt = DownloadToken.objects.from_media_file(self.user, mf)
        url = reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()["subtitle_files"] == [
            "https://b2.example.com/mybucket/tv/Show.Name/Show.Name.S01E01.mv-encoded.mp4.mv-encoded.mp4-0.vtt?sig=abc",
        ]

    def test_uuid_tv_token_links_video_subtitle_and_original_name(
        self, client, create_tv_media_file
    ):
        client.force_login(self.user)
        mf = create_tv_media_file(filename="Original.Name.mkv")
        mf.b2_uuid = uuid.uuid4()
        mf.subtitle_files = ["subtitle-uuid.vtt"]
        mf.save()
        mp = mf.media_path
        mp._path = f"b2://mybucket/tv/{mp.pk}/Show/"
        mp.save()
        dt = DownloadToken.objects.from_media_file(self.user, mf)
        response = client.get(
            reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "Original.Name.mkv"
        assert data["download_link"].endswith(f"tv/{mp.pk}/{mf.b2_uuid}.mkv?sig=abc")
        assert data["subtitle_files"] == [
            f"https://b2.example.com/mybucket/tv/{mp.pk}/subtitle-uuid.vtt?sig=abc"
        ]

    def test_form_upload_replay_keeps_subtitles_associated_per_video(
        self, client, create_tv_media_file
    ):
        client.force_login(self.user)
        first = create_tv_media_file(filename="Original.One.mp4")
        mp = first.media_path
        second = MediaFile.objects.create(
            media_path=mp, filename="Original.Two.mkv", display_name="Episode two"
        )
        mp._path = f"b2://mybucket/archive/{mp.pk}/Show/"
        mp.save()
        uploaded = [
            (first, uuid.uuid4(), [f"{uuid.uuid4()}.vtt", f"{uuid.uuid4()}.vtt"]),
            (second, uuid.uuid4(), [f"{uuid.uuid4()}.vtt"]),
        ]
        upload_url = reverse("mediaviewer:api:mediafile-list")
        for media_file, object_uuid, subtitles in uploaded:
            payload = {
                "filename": media_file.filename,
                "media_path": mp.pk,
                "b2_uuid": str(object_uuid),
                "size": 456,
                "subtitle_files": json.dumps(subtitles),
            }
            created = client.post(upload_url, data=payload)
            replay = client.post(upload_url, data=payload)

            assert created.status_code == 201, created.json()
            assert replay.status_code == 201
            assert replay.json()["pk"] == created.json()["pk"]
            assert created.json()["filename"] == media_file.filename
            assert created.json()["b2_uuid"] == str(object_uuid)
            assert created.json()["subtitle_files"] == subtitles

        assert set(uploaded[0][2]).isdisjoint(uploaded[1][2])
        for media_file, object_uuid, subtitles in uploaded:
            media_file.refresh_from_db()
            assert media_file.filename in ("Original.One.mp4", "Original.Two.mkv")
            assert str(media_file.b2_uuid) == str(object_uuid)
            assert media_file.subtitle_files == subtitles

            token = DownloadToken.objects.from_media_file(self.user, media_file)
            self.mock_b2_client.return_value.generate_presigned_url.reset_mock()
            response = client.get(
                reverse("mediaviewer:api:downloadtoken-detail", args=[token.guid])
            )

            assert response.status_code == 200
            data = response.json()
            assert data["original_filename"] == media_file.filename
            assert data["download_link"] == (
                f"https://b2.example.com/mybucket/archive/{mp.pk}/"
                f"{object_uuid}{Path(media_file.filename).suffix}?sig=abc"
            )
            assert data["subtitle_files"] == [
                f"https://b2.example.com/mybucket/archive/{mp.pk}/{name}?sig=abc"
                for name in subtitles
            ]
            assert [
                call.kwargs["key"]
                for call in self.mock_b2_client.return_value.generate_presigned_url.call_args_list
            ] == [
                f"archive/{mp.pk}/{object_uuid}{Path(media_file.filename).suffix}",
                *[f"archive/{mp.pk}/{name}" for name in subtitles],
            ]

    def test_uuid_movie_token_links_selected_file_and_keeps_token_filename(
        self, client, create_movie
    ):
        client.force_login(self.user)
        movie = create_movie()
        mp = movie.media_path
        mp._path = f"b2://mybucket/movies/{mp.pk}/Movie/"
        mp.filename = "Original.Movie.mkv"
        mp.save()
        mf = MediaFile.objects.create(
            media_path=mp,
            filename=mp.filename,
            b2_uuid=uuid.uuid4(),
            subtitle_files=["movie-subtitle.vtt"],
        )
        dt = DownloadToken.objects.from_movie(self.user, movie)
        response = client.get(
            reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == movie.name
        assert data["original_filename"] == "Original.Movie.mkv"
        assert data["download_link"].endswith(
            f"movies/{mp.pk}/{mf.b2_uuid}.mkv?sig=abc"
        )
        assert data["subtitle_files"] == [
            f"https://b2.example.com/mybucket/movies/{mp.pk}/movie-subtitle.vtt?sig=abc"
        ]

    def test_expired_b2_token_has_no_subtitle_files(self, client, create_movie):
        client.force_login(self.user)
        movie = create_movie()
        mp = movie.mediapath_set.first()
        mp._path = "b2://mybucket/movies/Movie.Name/"
        mp.filename = "Movie.Name.mp4"
        mp.subtitle_files = ["Movie.Name.mp4.mv-encoded.mp4-0.vtt"]
        mp.save()

        dt = DownloadToken.objects.from_movie(self.user, movie)
        dt.date_created = dt.date_created - timezone.timedelta(
            hours=settings.TOKEN_VALIDITY_LENGTH
        )
        dt.save()

        url = reverse("mediaviewer:api:downloadtoken-detail", args=[dt.guid])
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()["subtitle_files"] == []


@pytest.mark.django_db
class TestMediaPathCreate:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.user = create_user(is_staff=True)

    def test_create_tv_media_path_with_b2_path(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:tvmediapath-list")
        response = client.post(url, {"path": "b2://mybucket/tv/Show.Name/"})

        assert response.status_code == 200
        data = response.json()
        assert data["path"] == "b2://mybucket/tv/Show.Name/"
        assert data["bucket"] == "mybucket"
        assert data["b2_upload_prefix"] == f"tv/{data['pk']}/"
        assert data["filename"] is None
        assert TV.objects.count() == 1
        mp = MediaPath.objects.get(_path="b2://mybucket/tv/Show.Name/")
        assert mp.tv is not None

    def test_create_movie_media_path_with_b2_path_and_filename(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:moviemediapath-list")
        response = client.post(
            url,
            {"path": "b2://mybucket/movies/Movie.Name/", "filename": "Movie.Name.mp4"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["path"] == "b2://mybucket/movies/Movie.Name/"
        assert data["filename"] == "Movie.Name.mp4"
        assert Movie.objects.count() == 1
        mp = MediaPath.objects.get(_path="b2://mybucket/movies/Movie.Name/")
        assert mp.movie is not None
        assert mp.filename == "Movie.Name.mp4"

    def test_create_media_path_with_b2_path_missing_bucket(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:tvmediapath-list")
        response = client.post(url, {"path": "b2:///tv/Show.Name/"})

        assert response.status_code == 400

    def test_create_media_path_with_b2_path_missing_key(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:tvmediapath-list")
        response = client.post(url, {"path": "b2://mybucket/"})

        assert response.status_code == 400

    def test_create_media_path_is_idempotent(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:tvmediapath-list")
        first = client.post(url, {"path": "b2://mybucket/tv/Show.Name/"})
        second = client.post(url, {"path": "b2://mybucket/tv/Show.Name/"})

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["pk"] == second.json()["pk"]
        assert TV.objects.count() == 1
        assert MediaPath.objects.count() == 1

    def test_create_media_path_updates_filename_on_repost(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:moviemediapath-list")
        first = client.post(
            url,
            {"path": "b2://mybucket/movies/Movie.Name/", "filename": "Movie.Name.mp4"},
        )
        second = client.post(
            url,
            {"path": "b2://mybucket/movies/Movie.Name/", "filename": "Movie.Name.mkv"},
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["pk"] == second.json()["pk"]
        assert second.json()["filename"] == "Movie.Name.mkv"

    def test_create_movie_media_path_with_subtitle_files(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:moviemediapath-list")
        response = client.post(
            url,
            {
                "path": "b2://mybucket/movies/Movie.Name/",
                "filename": "Movie.Name.mp4",
                "subtitle_files": '["Movie.Name.mp4.mv-encoded.mp4-0.vtt", "Movie.Name.mp4.mv-encoded.mp4-1.vtt"]',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subtitle_files"] == [
            "Movie.Name.mp4.mv-encoded.mp4-0.vtt",
            "Movie.Name.mp4.mv-encoded.mp4-1.vtt",
        ]
        mp = MediaPath.objects.get(_path="b2://mybucket/movies/Movie.Name/")
        assert mp.subtitle_files == [
            "Movie.Name.mp4.mv-encoded.mp4-0.vtt",
            "Movie.Name.mp4.mv-encoded.mp4-1.vtt",
        ]

    def test_create_media_path_updates_subtitle_files_on_repost(self, client):
        client.force_login(self.user)
        url = reverse("mediaviewer:api:moviemediapath-list")
        first = client.post(
            url,
            {
                "path": "b2://mybucket/movies/Movie.Name/",
                "filename": "Movie.Name.mp4",
                "subtitle_files": '["Movie.Name.mp4.mv-encoded.mp4-0.vtt"]',
            },
        )
        second = client.post(
            url,
            {
                "path": "b2://mybucket/movies/Movie.Name/",
                "filename": "Movie.Name.mp4",
                "subtitle_files": '["Movie.Name.mp4.mv-encoded.mp4-1.vtt"]',
            },
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["pk"] == second.json()["pk"]
        assert second.json()["subtitle_files"] == [
            "Movie.Name.mp4.mv-encoded.mp4-1.vtt"
        ]

    def test_uuid_movie_filename_cannot_change_via_path_post(
        self, client, create_movie, mocker
    ):
        client.force_login(self.user)
        movie = create_movie()
        mp = movie.media_path
        mp._path = f"b2://bucket/movies/{mp.pk}/Movie/"
        mp.filename = "Original.Movie.mkv"
        mp.save()
        MediaFile.objects.create(
            media_path=mp, filename=mp.filename, b2_uuid=uuid.uuid4()
        )
        client_mock = mocker.patch("mediaviewer.b2.get_b2_client").return_value
        client_mock.generate_presigned_url.return_value = "https://video"
        url = reverse("mediaviewer:api:moviemediapath-list")

        same = client.post(url, {"path": mp._path, "filename": "Original.Movie.mkv"})
        changed = client.post(url, {"path": mp._path, "filename": "Renamed.mkv"})

        assert same.status_code == 200
        assert changed.status_code == 400
        mp.refresh_from_db()
        assert mp.filename == "Original.Movie.mkv"
        mp.movie.downloadLink("guid")
        client_mock.generate_presigned_url.assert_called_once_with(
            bucket="bucket",
            key=f"movies/{mp.pk}/{mp.mediafile_set.get().b2_uuid}.mkv",
            expires_in=None,
        )

    def test_uuid_movie_filename_cannot_change_via_serializer_update(
        self, client, create_movie
    ):
        client.force_login(self.user)
        movie = create_movie()
        mp = movie.media_path
        mp._path = f"b2://bucket/movies/{mp.pk}/Movie/"
        mp.filename = "Original.Movie.mkv"
        mp.save()
        MediaFile.objects.create(
            media_path=mp, filename=mp.filename, b2_uuid=uuid.uuid4()
        )
        url = reverse("mediaviewer:api:moviemediapath-detail", args=[mp.pk])

        for method in (client.patch, client.put):
            response = method(
                url,
                data={"filename": "Renamed.mkv"},
                content_type="application/json",
            )
            assert response.status_code == 400
            assert "Cannot change filename" in str(response.json())
            mp.refresh_from_db()
            assert mp.filename == "Original.Movie.mkv"
