from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from mediaviewer.models.path import Path

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
