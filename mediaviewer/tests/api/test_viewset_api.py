import pytest

from django.urls import reverse
from mediaviewer.models.downloadtoken import DownloadToken


@pytest.mark.django_db
@pytest.mark.parametrize(
    'use_movie', (True, False))
@pytest.mark.parametrize(
    'use_regular_user', (True, False))
class TestDownloadToken:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user):
        self.user = create_user(is_staff=True)
        self.regular_user = create_user()

    def test_detail(self,
                    client,
                    use_movie,
                    use_regular_user,
                    create_movie,
                    create_tv_media_file):
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

        url = reverse(
            "mediaviewer:api:downloadtoken-detail", args=[dt.guid]
        )
        response = client.get(url)
        if not use_regular_user:
            assert response.status_code == 200

            json_data = response.json()
            assert dt.guid == json_data['guid']
            assert dt.user.username == json_data['username']

            assert dt.ref_obj.full_name == json_data['displayname']
        else:
            assert response.status_code == 403
