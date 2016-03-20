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

    def test_create_tv_path(self):
        self.data = {'localpath': '/path/to/folder',
                     'remotepath': '/path/to/folder',
                     'server': 'a.server',
                     'skip': False,
                     }
        response = self.client.post(reverse('mediaviewer:api:path-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        expected_dict = self.data
        expected_dict.update({'is_movie': False})

        pk = response.data['pk']
        path = Path.objects.get(pk=pk)
        for k,v in expected_dict.items():
            expected = v
            actual = getattr(path, k)
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_get_path_detail(self):
        response = self.client.get(reverse('mediaviewer:api:path-detail', args=[self.tvPath.id]))
        for k,v in response.data.items():
            actual = v
            expected = getattr(self.tvPath, k)
            expected = expected(self.tvPath) if hasattr(expected, '__call__') else expected
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_get_path_list(self):
        response = self.client.get(reverse('mediaviewer:api:path-list'))
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        expected = {'count': 1,
                    'next': None,
                    'previous': None,
                    'results': [{'pk': self.tvPath.id,
                                'localpath': '/some/local/path',
                                'remotepath': '/some/local/path',
                                'server': 'a.server',
                                'skip': False,
                                'number_of_unwatched_shows': 0,
                                'is_movie': False,
                                }],
                    }
        actual = dict(response.data)
        actual['results'] = map(dict, actual['results'])

        self.assertEquals(expected, actual)

class MoviePathViewSetTests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        self.client.login(username='test_user', password='password')

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

    def test_create_moviepath(self):
        self.data = {'localpath': '/path/to/folder',
                     'remotepath': '/path/to/folder',
                     'server': 'a.server',
                     'skip': False,
                     }
        response = self.client.post(reverse('mediaviewer:api:moviepath-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        expected_dict = self.data
        expected_dict.update({'is_movie': True})

        pk = response.data['pk']
        path = Path.objects.get(pk=pk)
        for k,v in expected_dict.items():
            expected = v
            actual = getattr(path, k)
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_get_moviepath(self):
        response = self.client.get(reverse('mediaviewer:api:moviepath-detail', args=[self.moviePath.id]))
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        for k,v in response.data.items():
            actual = v
            expected = getattr(self.moviePath, k)
            expected = expected(self.moviePath) if hasattr(expected, '__call__') else expected
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))
