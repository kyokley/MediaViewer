from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

#from mediaviewer.api.viewset import MovieFileViewSet

class MovieFileViewSetTests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_superuser('test_user',
                                             'test@user.com',
                                             'password')
        self.client.login(username='test_user', password='password')
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     }

    def test_create_moviefile(self):
        response = self.client.post(reverse('mediaviewer:api:movie-list'), self.data)
        if response.status_code == 500:
            assert False
