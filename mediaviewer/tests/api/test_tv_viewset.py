import pytest

from django.urls import reverse


@pytest.mark.django_db
class TestTv:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv, create_user):
        self.user = create_user(is_staff=True)

        self.tv_shows = [create_tv()
                         for i in range(3)]

    def test_detail(self, client):
        client.force_login(self.user)

        for tv in self.tv_shows:
            url = reverse(
                "mediaviewer:api:tv-detail", args=[tv.pk]
            )
            response = client.get(url)
            assert response.status_code == 200

            json_data = response.json()
            assert tv.name == json_data['name']
            assert tv.pk == json_data['pk']

    def test_list(self, client):
        client.force_login(self.user)

        url = reverse(
            "mediaviewer:api:tv-list"
        )
        response = client.get(url)
        assert response.status_code == 200

        json_data = response.json()
        expected = {'count': 3,
                    'next': None,
                    'previous': None,
                    'results': [
                        {'pk': self.tv_shows[0].pk, 'name': self.tv_shows[0].name, 'number_of_unwatched_shows': 0},
                        {'pk': self.tv_shows[1].pk, 'name': self.tv_shows[1].name, 'number_of_unwatched_shows': 0},
                        {'pk': self.tv_shows[2].pk, 'name': self.tv_shows[2].name, 'number_of_unwatched_shows': 0}]}
        assert expected == json_data
