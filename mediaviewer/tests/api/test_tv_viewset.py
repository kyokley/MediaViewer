import pytest
from django.urls import reverse
from mediaviewer.models.tv import TV


@pytest.mark.django_db
@pytest.mark.parametrize('is_staff',
                         (True, False))
class TestTv:
    @pytest.fixture(autouse=True)
    def setUp(self, client, create_tv, create_user):
        self.client = client
        self.user = create_user(is_staff=True)
        self.non_staff_user = create_user(is_staff=False)

        self.tv_shows = [create_tv() for i in range(3)]

    def test_detail(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        for tv in self.tv_shows:
            url = reverse("mediaviewer:api:tv-detail", args=[tv.pk])
            response = self.client.get(url)
            assert response.status_code == 200

            json_data = response.json()
            assert tv.name == json_data["name"]
            assert tv.pk == json_data["pk"]
            assert str(tv.media_path.path) == json_data['media_paths'][0]['path']
            assert tv.finished == json_data['finished']

    def test_list(self, is_staff):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")
        response = self.client.get(url)
        assert response.status_code == 200

        json_data = response.json()
        expected = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": self.tv_shows[0].pk,
                    "name": self.tv_shows[0].name,
                    "number_of_unwatched_shows": 0,
                    'media_paths': [{'path': str(self.tv_shows[0].media_path.path),
                                     'pk': self.tv_shows[0].media_path.pk}],
                    'finished': self.tv_shows[0].finished,
                },
                {
                    "pk": self.tv_shows[1].pk,
                    "name": self.tv_shows[1].name,
                    "number_of_unwatched_shows": 0,
                    'media_paths': [{'path': str(self.tv_shows[1].media_path.path),
                                     'pk': self.tv_shows[1].media_path.pk}],
                    'finished': self.tv_shows[1].finished,
                },
                {
                    "pk": self.tv_shows[2].pk,
                    "name": self.tv_shows[2].name,
                    "number_of_unwatched_shows": 0,
                    'media_paths': [{'path': str(self.tv_shows[2].media_path.path),
                                     'pk': self.tv_shows[2].media_path.pk}],
                    'finished': self.tv_shows[2].finished,
                },
            ],
        }
        assert expected == json_data

    @pytest.mark.parametrize(
        'include_name',
        (True, False))
    def test_create_new(self, is_staff, include_name):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        url = reverse("mediaviewer:api:tv-list")

        post_data = {'media_path': '/path/to/dir'}

        if include_name:
            post_data['name'] = 'test_name'

        response = self.client.post(url, data=post_data)

        if is_staff:
            json_data = response.json()

            assert TV.objects.count() == 4

            new_tv_obj = TV.objects.get(pk=json_data['pk'])
            if include_name:
                assert new_tv_obj.name == 'test_name'
            else:
                assert new_tv_obj.name == 'dir'

            assert str(new_tv_obj.media_path.path) == '/path/to/dir'
            assert not new_tv_obj.finished
        else:
            assert response.status_code == 403
            assert TV.objects.count() == 3

    def test_create_existing(self, is_staff, create_tv):
        if not is_staff:
            self.client.force_login(self.non_staff_user)
        else:
            self.client.force_login(self.user)

        new_tv = create_tv()

        url = reverse("mediaviewer:api:tv-list")

        post_data = {'name': new_tv.name,
                     'media_path': str(new_tv.media_path.path)}

        response = self.client.post(url, data=post_data)

        assert TV.objects.count() == 4
        if is_staff:
            json_data = response.json()

            assert new_tv.pk == json_data['pk']
            assert new_tv.name == json_data['name']
            assert str(new_tv.media_path.path) == json_data['media_paths'][0]['path']
            assert new_tv.finished == json_data['finished']
        else:
            assert response.status_code == 403
