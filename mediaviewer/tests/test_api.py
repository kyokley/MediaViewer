from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from mediaviewer.models.path import Path

#from mediaviewer.api.viewset import MovieFileViewSet

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
        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class PathViewSetTests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        self.client.login(username='test_user', password='password')

        self.newPath = Path()
        self.newPath.localpathstr = 'local.path.str'
        self.newPath.remotepathstr = 'remote.path.str'
        self.newPath.skip = False
        self.newPath.is_movie = False
        self.newPath.server = 'a.server'
        self.newPath.save()

    def test_create_tv_path(self):
        self.data = {'localpath': '/path/to/folder',
                     'remotepath': '/path/to/folder',
                     'server': 'a.server',
                     'skip': False,
                     'is_movie': False,
                     }
        response = self.client.post(reverse('mediaviewer:api:path-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        pk = response.data['pk']
        path = Path.objects.get(pk=pk)
        for k,v in self.data.items():
            expected = v
            actual = getattr(path, k)
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_create_movie_path(self):
        self.data = {'localpath': '/path/to/folder',
                     'remotepath': '/path/to/folder',
                     'server': 'a.server',
                     'skip': False,
                     'is_movie': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:path-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        pk = response.data['pk']
        path = Path.objects.get(pk=pk)
        for k,v in self.data.items():
            expected = v
            actual = getattr(path, k)
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_get_path(self):
        response = self.client.get(reverse('mediaviewer:api:path-detail', args=[self.newPath.id]))
        for k,v in response.data.items():
            actual = v
            expected = getattr(self.newPath, k)
            expected = expected(self.newPath) if hasattr(expected, '__call__') else expected
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))
