from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from mediaviewer.models.path import Path
from mediaviewer.models.file import File

class MovieFileViewSetTests(APITestCase):
    def setUp(self):
        self.tvPath = Path()
        self.tvPath.localpathstr = '/some/local/path'
        self.tvPath.remotepathstr = '/some/local/path'
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = 'a.server'
        self.tvPath.save()

        self.tvFile = File()
        self.tvFile.filename = 'some.tv.show'
        self.tvFile.skip = False
        self.tvFile.finished = True
        self.tvFile.size = 100
        self.tvFile.streamable = True
        self.tvFile.path = self.tvPath
        self.tvFile.hide = False
        self.tvFile.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = '/another/local/path'
        self.moviePath.remotepathstr = '/another/local/path'
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = 'a.server'
        self.moviePath.save()

        self.movieFile = File()
        self.movieFile.filename = 'some.movie.show'
        self.movieFile.skip = False
        self.movieFile.finished = True
        self.movieFile.size = 0
        self.movieFile.streamable = True
        self.movieFile.path = self.moviePath
        self.movieFile.hide = False
        self.movieFile.save()

        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        self.client.login(username='test_user', password='password')

    def test_create_moviefile_using_tvpath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'path': self.tvPath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:movie-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_moviefile_using_moviepath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'path': self.moviePath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:movie-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_update_valid_moviefile(self):
        self.data = {'filename': 'new.movie.filename',
                     'skip': True,
                     'finished': True,
                     'size': 0,
                     'streamable': True,
                     }
        response = self.client.put(reverse('mediaviewer:api:movie-detail', args=[self.movieFile.id]), self.data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        movieFile = File.objects.get(pk=response.data['pk'])
        for k,v in self.data.items():
            expected = v
            actual = getattr(movieFile, k)
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_update_invalid_moviefile(self):
        self.data = {'filename': 'new.movie.filename',
                     'skip': True,
                     'finished': True,
                     'size': 0,
                     'streamable': True,
                     }
        response = self.client.put(reverse('mediaviewer:api:movie-detail', args=[self.tvFile.id]), self.data)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

class TvFileViewSetTests(APITestCase):
    def setUp(self):
        self.tvPath = Path()
        self.tvPath.localpathstr = '/some/local/path'
        self.tvPath.remotepathstr = '/some/local/path'
        self.tvPath.skip = False
        self.tvPath.is_movie = False
        self.tvPath.server = 'a.server'
        self.tvPath.save()

        self.anotherTvPath = Path()
        self.anotherTvPath.localpathstr = '/path/to/folder'
        self.anotherTvPath.remotepathstr = '/path/to/folder'
        self.anotherTvPath.skip = False
        self.anotherTvPath.is_movie = False
        self.anotherTvPath.server = 'a.server'
        self.anotherTvPath.save()

        self.tvFile = File()
        self.tvFile.filename = 'some.tv.show'
        self.tvFile.skip = False
        self.tvFile.finished = True
        self.tvFile.size = 100
        self.tvFile.streamable = True
        self.tvFile.path = self.tvPath
        self.tvFile.hide = False
        self.tvFile.save()

        self.anotherTvFile = File()
        self.anotherTvFile.filename = 'another.tv.show'
        self.anotherTvFile.skip = False
        self.anotherTvFile.finished = True
        self.anotherTvFile.size = 100
        self.anotherTvFile.streamable = True
        self.anotherTvFile.path = self.anotherTvPath
        self.anotherTvFile.hide = False
        self.anotherTvFile.save()

        self.moviePath = Path()
        self.moviePath.localpathstr = '/another/local/path'
        self.moviePath.remotepathstr = '/another/local/path'
        self.moviePath.skip = False
        self.moviePath.is_movie = True
        self.moviePath.server = 'a.server'
        self.moviePath.save()

        self.movieFile = File()
        self.movieFile.filename = 'some.movie.show'
        self.movieFile.skip = False
        self.movieFile.finished = True
        self.movieFile.size = 0
        self.movieFile.streamable = True
        self.movieFile.path = self.moviePath
        self.movieFile.hide = False
        self.movieFile.save()

        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')
        self.client.login(username='test_user', password='password')

    def test_get_tvfiles_by_pathid(self):
        response = self.client.get(reverse('mediaviewer:api:tv-list'), {'pathid': self.tvPath.id})
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        expected = {'count': 1,
                    'next': None,
                    'previous': None,
                    'results': [{'pk': self.tvFile.id,
                                 'path': self.tvFile.path.id,
                                 'filename': 'some.tv.show',
                                 'skip': False,
                                 'finished': True,
                                 'size': self.tvFile.size,
                                 'streamable': True,
                                 'localpath': self.tvFile.path.localpathstr,
                                 'ismovie': self.tvFile.isMovie()
                                 }],
                    }
        actual = dict(response.data)
        actual['results'] = map(dict, actual['results'])

        self.assertEquals(expected, actual)

    def test_create_tvfile_using_tvpath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'path': self.tvPath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:tv-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_create_tvfile_using_moviepath(self):
        self.data = {'filename': 'new file',
                     'skip': False,
                     'finished': True,
                     'size': 100,
                     'path': self.moviePath.id,
                     'streamable': True,
                     }
        response = self.client.post(reverse('mediaviewer:api:tv-list'), self.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_valid_tvfile(self):
        self.data = {'filename': 'new.tv.filename',
                     'skip': True,
                     'finished': True,
                     'size': 0,
                     'streamable': True,
                     }
        response = self.client.put(reverse('mediaviewer:api:tv-detail', args=[self.tvFile.id]), self.data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        tvFile = File.objects.get(pk=response.data['pk'])
        for k,v in self.data.items():
            expected = v
            actual = getattr(tvFile, k)
            self.assertEquals(expected, actual, 'attr: %s expected: %s actual: %s' % (k, expected, actual))

    def test_update_invalid_tvfile(self):
        self.data = {'filename': 'new.tv.filename',
                     'skip': True,
                     'finished': True,
                     'size': 0,
                     'streamable': True,
                     }
        response = self.client.put(reverse('mediaviewer:api:tv-detail', args=[self.movieFile.id]), self.data)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
