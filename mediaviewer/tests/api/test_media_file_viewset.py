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
