import pytest

from django.urls import reverse
from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.django_db
@pytest.mark.parametrize(
    'use_movie', (True, False))
class TestDownloadToken:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user(is_staff=True)

    def test_detail(self,
                    client,
                    use_movie,
                    create_movie,
                    create_tv_media_file):
        client.force_login(self.user)

        if use_movie:
            movie = create_movie()
            dt = DownloadToken.objects.from_movie(self.user, movie)
        else:
            mf = create_tv_media_file()
            dt = DownloadToken.objects.from_media_file(self.user, mf)

        url = reverse(
            "mediaviewer:api:downloadtoken-detail", args=[dt.guid]
        )
        response = client.get(url)
        assert response.status_code == 200

        json_data = response.json()
        assert dt.guid == json_data['guid']
        assert dt.user.username == json_data['username']

        assert dt.ref_obj.full_name == json_data['displayname']
