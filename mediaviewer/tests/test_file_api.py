from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from mediaviewer.models.path import Path

class MovieFileViewSetTests(APITestCase):
    def setUp(self):
        self.tvPath = Path()
        self.tvPath.localpathstr = '/some/local/path'
        self.tvPath.remotepathstr = '/some/local/path'
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = 'a.server'
        self.tvPath.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = '/another/local/path'
        self.moviePath.remotepathstr = '/another/local/path'
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = 'a.server'
        self.moviePath.save()

        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        self.client.login(username='test_user', password='password')

    def test_create_moviefile_using_tvpath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'pathid': self.tvPath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:movie-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_moviefile_using_moviepath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'pathid': self.moviePath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:movie-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

class TvFileViewSetTests(APITestCase):
    def setUp(self):
        self.tvPath = Path()
        self.tvPath.localpathstr = '/some/local/path'
        self.tvPath.remotepathstr = '/some/local/path'
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = 'a.server'
        self.tvPath.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = '/another/local/path'
        self.moviePath.remotepathstr = '/another/local/path'
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = 'a.server'
        self.moviePath.save()

        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        self.client.login(username='test_user', password='password')

    def test_create_tvfile_using_tvpath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'pathid': self.tvPath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:tv-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_create_tvfile_using_moviepath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'pathid': self.moviePath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:tv-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
