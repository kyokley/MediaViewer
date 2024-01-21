import pytest

from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize('is_staff',
                         (True, False))
@pytest.mark.parametrize('use_tv',
                         (True, False))
class TestMediaPath:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_movie, create_user):
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)

        self.tv = create_tv()
        self.movie = create_movie()

    def test_detail(self, is_staff, use_tv):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        if use_tv:
            ref_media = self.tv
        else:
            ref_media = self.movie

        url = reverse(f"mediaviewer:api:{'tv' if use_tv else 'movie'}mediapath-detail", args=[ref_media.media_path.pk])

        response = self.client.get(url)
        assert response.status_code == 200

        json_data = response.json()
        assert json_data['path'] == str(ref_media.media_path.path)

        if use_tv:
            assert json_data['tv'] == ref_media.pk
            assert json_data['movie'] is None
        else:
            assert json_data['tv'] is None
            assert json_data['movie'] == ref_media.pk
