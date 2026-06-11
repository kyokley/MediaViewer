import pytest
from django.urls import reverse


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
