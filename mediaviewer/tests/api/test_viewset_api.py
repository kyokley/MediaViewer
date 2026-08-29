import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from mediaviewer.models import MediaPath, Movie, TV
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
