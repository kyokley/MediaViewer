import pytest
from django.urls import reverse
from mediaviewer.models import MediaFile
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
        else:
            assert response.status_code == 403


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
