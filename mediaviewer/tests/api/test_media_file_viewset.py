import pytest
import uuid
from django.urls import reverse
from mediaviewer.models import FilenameScrapeFormat, MediaFile
from mediaviewer.models.apikey import ApiKey


@pytest.mark.django_db
@pytest.mark.parametrize("is_staff", (True, False))
class TestMediaFile:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_user, create_tv, create_movie):
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)

        self.tv = create_tv()
        self.movie = create_movie()

    @pytest.mark.parametrize("use_tv", (True, False))
    def test_create(self, is_staff, use_tv):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        if use_tv:
            ref_media = self.tv
        else:
            ref_media = self.movie

        url = reverse("mediaviewer:api:mediafile-list")

        payload = {
            "filename": "test_filename",
            "media_path": ref_media.media_path.pk,
            "size": 100,
            "subtitle_files": '["test_filename.mv-encoded.mp4-0.vtt"]',
        }
        response = self.client.post(url, data=payload)

        if is_staff:
            assert response.status_code == 201

            json_data = response.json()

            assert json_data["filename"] == "test_filename"
            assert json_data["media_path"] == ref_media.media_path.pk
            if use_tv:
                assert not json_data["ismovie"]
            else:
                assert json_data["ismovie"]
            assert json_data["size"] == 100
            assert json_data["subtitle_files"] == ["test_filename.mv-encoded.mp4-0.vtt"]
        else:
            assert response.status_code == 403

    def test_uuid_upload_replay_and_movie_publication(self, is_staff):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        self.client.force_login(self.user)
        mp = self.movie.media_path
        mp._path = f"b2://bucket/movies/{mp.pk}/"
        mp.filename = None
        mp.save()
        object_uuid = str(uuid.uuid4())
        payload = {
            "filename": "Original.Movie.mkv",
            "media_path": mp.pk,
            "b2_uuid": object_uuid,
            "size": 123,
            "subtitle_files": '["sub-id.vtt"]',
        }
        url = reverse("mediaviewer:api:mediafile-list")
        first = self.client.post(url, data=payload, format="json")
        replay = self.client.post(url, data=payload, format="json")

        assert first.status_code == 201, first.json()
        assert replay.status_code == 201
        assert replay.json()["pk"] == first.json()["pk"]
        mp.refresh_from_db()
        assert mp.filename == "Original.Movie.mkv"
        assert mp.subtitle_files == ["sub-id.vtt"]

    def test_uuid_tv_upload_persists_episode_and_blank_poster(self, is_staff, mocker):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        self.client.force_login(self.user)
        mocker.patch("mediaviewer.thetvdb.resolve_series_name")
        mp = self.tv.media_path
        mp._path = f"b2://bucket/tv/{mp.pk}/"
        mp.save(update_fields=("_path",))
        payload = {
            "filename": "Original.Show.S01E02.mkv",
            "media_path": mp.pk,
            "b2_uuid": str(uuid.uuid4()),
        }
        url = reverse("mediaviewer:api:mediafile-list")

        response = self.client.post(url, data=payload, format="json")

        assert response.status_code == 201, response.json()
        media_file = MediaFile.objects.get(pk=response.json()["pk"])
        assert media_file.filename == payload["filename"]
        assert str(media_file.b2_uuid) == payload["b2_uuid"]
        assert (media_file.season, media_file.episode) == (1, 2)
        assert media_file._poster_id
        assert media_file.poster.episodename == ""
        assert media_file.display_name == "S01 E02"
        assert FilenameScrapeFormat.objects.count() == 0

        poster = media_file.poster
        poster.episodename = "Retained title"
        poster.save(update_fields=("episodename",))
        replay = self.client.post(url, data=payload, format="json")

        assert replay.status_code == 201
        media_file.refresh_from_db()
        assert replay.json()["pk"] == media_file.pk
        assert media_file._poster_id == poster.pk
        assert media_file.poster.episodename == "Retained title"

    def test_uuid_upload_attaches_and_parses_existing_file(self, is_staff):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        self.client.force_login(self.user)
        media_file = MediaFile.objects.create(
            media_path=self.tv.media_path,
            filename="Attach.Show.S02E03.mkv",
            display_name="Existing name",
        )
        payload = {
            "filename": media_file.filename,
            "media_path": self.tv.media_path.pk,
            "b2_uuid": str(uuid.uuid4()),
        }

        response = self.client.post(
            reverse("mediaviewer:api:mediafile-list"), data=payload, format="json"
        )

        assert response.status_code == 201, response.json()
        media_file.refresh_from_db()
        assert response.json()["pk"] == media_file.pk
        assert media_file.filename == payload["filename"]
        assert str(media_file.b2_uuid) == payload["b2_uuid"]
        assert (media_file.season, media_file.episode) == (2, 3)
        assert media_file._poster_id
        assert media_file.display_name == "S02 E03"

    def test_uuid_validation_and_conflicting_owner(self, is_staff):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mediafile-list")
        payload = {
            "filename": "episode.mp4",
            "media_path": self.tv.media_path.pk,
            "b2_uuid": "not-a-uuid",
        }
        assert self.client.post(url, data=payload, format="json").status_code == 400

        payload["b2_uuid"] = str(uuid.uuid4())
        first = self.client.post(url, data=payload, format="json")
        assert first.status_code == 201
        original = MediaFile.objects.get(pk=first.json()["pk"])
        unparseable = original
        assert unparseable.filename == "episode.mp4"
        assert unparseable.season is None
        assert unparseable.episode is None
        assert unparseable._poster_id is None
        payload["media_path"] = self.movie.media_path.pk
        assert self.client.post(url, data=payload, format="json").status_code == 400
        original.refresh_from_db()
        assert original.media_path_id == self.tv.media_path.pk
        assert original.filename == "episode.mp4"
        assert original.b2_uuid == uuid.UUID(payload["b2_uuid"])

    def test_movie_uuid_upload_rejects_second_primary(self, is_staff):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        self.client.force_login(self.user)
        mp = self.movie.media_path
        url = reverse("mediaviewer:api:mediafile-list")
        first = {
            "filename": "Movie.mkv",
            "media_path": mp.pk,
            "b2_uuid": str(uuid.uuid4()),
        }
        assert self.client.post(url, data=first, format="json").status_code == 201
        second = {**first, "b2_uuid": str(uuid.uuid4())}
        assert self.client.post(url, data=second, format="json").status_code == 400

    def test_uuid_upload_identity_cannot_be_changed(self, is_staff):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mediafile-list")
        created = self.client.post(
            url,
            {
                "filename": "episode.mp4",
                "media_path": self.tv.media_path.pk,
                "b2_uuid": str(uuid.uuid4()),
            },
            format="json",
        )
        assert created.status_code == 201
        from mediaviewer.api.serializers import MediaFileSerializer
        from rest_framework.exceptions import ValidationError

        instance = MediaFile.objects.get(pk=created.json()["pk"])
        serializer = MediaFileSerializer(
            instance, data={"filename": "episode.mkv"}, partial=True
        )
        assert serializer.is_valid()
        with pytest.raises(ValidationError, match="identity of a published B2 upload"):
            serializer.save()

    def test_update_cannot_acquire_uuid(self, is_staff):
        if not is_staff:
            pytest.skip("UUID upload requires staff write access")
        from mediaviewer.api.serializers import MediaFileSerializer
        from rest_framework.exceptions import ValidationError

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mediafile-list")
        owner = self.client.post(
            url,
            {
                "filename": "owner.mp4",
                "media_path": self.tv.media_path.pk,
                "b2_uuid": str(uuid.uuid4()),
            },
            format="json",
        )
        assert owner.status_code == 201
        untracked = MediaFile.objects.create(
            media_path=self.movie.media_path, filename="untracked.mp4"
        )
        serializer = MediaFileSerializer(
            untracked, data={"b2_uuid": owner.json()["b2_uuid"]}, partial=True
        )
        assert serializer.is_valid()
        with pytest.raises(ValidationError, match="Use POST"):
            serializer.save()
        untracked.refresh_from_db()
        assert untracked.b2_uuid is None


@pytest.mark.django_db
class TestMediaFileAutoplay:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv_media_file, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.mf = create_tv_media_file()

    def test_retrieve(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-autoplay-detail", args=[self.mf.pk])
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        assert "link" in json_data
        assert json_data["link"] is not None

    def test_retrieve_non_staff_can_read(self):
        """Non-staff authenticated users can read (safe method)."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:mcp-autoplay-detail", args=[self.mf.pk])
        response = self.client.get(url)
        assert response.status_code == 200

    def test_retrieve_not_found(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-autoplay-detail", args=[99999])
        response = self.client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestMCPMediaFile:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv_media_file, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.tv = create_tv()
        self.other_tv = create_tv()
        self.mf1 = create_tv_media_file(tv=self.tv, filename="ep1.mp4")
        self.mf2 = create_tv_media_file(tv=self.tv, filename="ep2.mp4")
        self.other_mf = create_tv_media_file(tv=self.other_tv, filename="other.mp4")

    def test_list_requires_tv_id(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-mediafile-list")
        response = self.client.get(url)
        assert response.status_code == 400
        assert any("tv_id" in str(err) for err in response.json())

    def test_list_filters_by_tv_id(self):
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-mediafile-list")
        response = self.client.get(url, {"tv_id": self.tv.pk})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.mf1.pk in pks
        assert self.mf2.pk in pks
        assert self.other_mf.pk not in pks

    def test_list_non_staff_can_read(self):
        """Non-staff authenticated users can read (safe method)."""
        self.client.force_login(self.non_staff_user)
        url = reverse("mediaviewer:api:mcp-mediafile-list")
        response = self.client.get(url, {"tv_id": self.tv.pk})
        assert response.status_code == 200

    def test_hidden_mcp_media_files_excluded(self):
        """MCP media files list excludes hidden files."""
        MediaFile.objects.filter(pk=self.mf1.pk).update(hide=True)

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-mediafile-list")
        response = self.client.get(url, {"tv_id": self.tv.pk})
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data]
        assert self.mf1.pk not in pks
        assert self.mf2.pk in pks


@pytest.mark.django_db
class TestMCPMovieAutoplay:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_movie_media_file, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.mf = create_movie_media_file()

    def test_retrieve(self):
        """MCP movie autoplay returns a download link."""
        self.client.force_login(self.user)
        url = reverse(
            "mediaviewer:api:mcp-movie-autoplay-detail", args=[self.mf.movie.pk]
        )
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        assert "link" in json_data
        assert json_data["link"] is not None

    def test_retrieve_non_staff_can_read(self):
        """Non-staff authenticated users can read MCP movie autoplay."""
        self.client.force_login(self.non_staff_user)
        url = reverse(
            "mediaviewer:api:mcp-movie-autoplay-detail", args=[self.mf.movie.pk]
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_retrieve_not_found(self):
        """MCP movie autoplay returns 404 for non-existent movie."""
        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mcp-movie-autoplay-detail", args=[99999])
        response = self.client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestAPIKeyAuthentication:
    """Tests for IsStaffReadOnlyOrCheckAPIKey permission via MCP autoplay endpoint."""

    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv_media_file, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.staff_user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)
        self.mf = create_tv_media_file()
        self.url = reverse("mediaviewer:api:mcp-autoplay-detail", args=[self.mf.pk])

    def _create_api_key(self, user):
        """Create an ApiKey for a user."""
        return ApiKey.objects.create(user=user)

    def test_valid_api_key_authenticates(self):
        """A valid API key in the header authenticates the request."""
        api_key = self._create_api_key(self.non_staff_user)
        response = self.client.get(self.url, HTTP_API_KEY=api_key.key)
        assert response.status_code == 200
        json_data = response.json()
        assert "link" in json_data

    def test_invalid_api_key_returns_401(self):
        """An invalid API key returns 401 (unauthenticated)."""
        response = self.client.get(self.url, HTTP_API_KEY="invalid-key-12345")
        assert response.status_code == 401

    def test_inactive_user_with_valid_api_key_returns_401(self):
        """An inactive user with a valid API key gets 401 (unauthenticated)."""
        api_key = self._create_api_key(self.non_staff_user)
        self.non_staff_user.is_active = False
        self.non_staff_user.save()

        response = self.client.get(self.url, HTTP_API_KEY=api_key.key)
        assert response.status_code == 401

    def test_api_key_case_insensitive(self):
        """API key lookup is case-insensitive."""
        api_key = self._create_api_key(self.non_staff_user)
        response = self.client.get(self.url, HTTP_API_KEY=api_key.key.upper())
        assert response.status_code == 200

    def test_staff_user_can_access_without_api_key(self):
        """Staff users can access without providing an API key."""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_non_staff_authenticated_can_access_without_api_key(self):
        """Non-staff authenticated users can access safe methods without API key."""
        self.client.force_login(self.non_staff_user)
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_unauthenticated_no_api_key_returns_401(self):
        """Unauthenticated users without API key get 401 (unauthenticated)."""
        response = self.client.get(self.url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestMediaFileHiddenFilter:
    """Tests that MediaFileViewSet filters out hidden=False media files."""

    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv_media_file, create_tv, create_user, mocker):
        mocker.patch("mediaviewer.models.media.Media._populate_poster")
        self.client = client
        self.user = create_user(is_staff=True)
        self.tv = create_tv()
        self.hidden_tv = create_tv()

        self.visible_mf = create_tv_media_file(tv=self.tv, filename="visible.mp4")
        self.hidden_mf = create_tv_media_file(tv=self.hidden_tv, filename="hidden.mp4")

    def test_hidden_files_excluded(self):
        """Listing MediaFiles excludes hidden files."""
        MediaFile.objects.filter(pk=self.hidden_mf.pk).update(hide=True)

        self.client.force_login(self.user)
        url = reverse("mediaviewer:api:mediafile-list")
        response = self.client.get(url)
        assert response.status_code == 200
        json_data = response.json()
        pks = [item["pk"] for item in json_data["results"]]
        assert self.visible_mf.pk in pks
        assert self.hidden_mf.pk not in pks
