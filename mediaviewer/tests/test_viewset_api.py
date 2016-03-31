from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from datetime import datetime
import pytz

class DownloadTokenViewSetTests(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_superuser('test_user',
                                                       'test@user.com',
                                                       'password')

        self.user_settings = UserSettings()
        self.user_settings.user = self.test_user
        self.user_settings.ip_format = 'bangup'
        self.user_settings.can_download = True
        self.user_settings.site_theme = 'darkly'
        self.user_settings.auto_download = True
        self.user_settings.datecreated = datetime.now(pytz.timezone('US/Central'))
        self.user_settings.dateedited = datetime.now(pytz.timezone('US/Central'))
        self.user_settings.save()

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

        self.download_token = DownloadToken()
        self.download_token.guid = 'some unique id'
        self.download_token.user = self.test_user
        self.download_token.path = '/path/to/file'
        self.download_token.file = self.tvFile
        self.download_token.filename = 'name.of.file'
        self.download_token.ismovie = False
        self.download_token.waitertheme = 'default'
        self.download_token.displayname = 'Scraped Filename'
        self.download_token.datecreated = datetime.now(pytz.timezone('US/Central'))
        self.download_token.dateedited = datetime.now(pytz.timezone('US/Central'))
        self.download_token.save()

        self.client.login(username='test_user', password='password')

    def test_get_download_token(self):
        response = self.client.get(reverse('mediaviewer:api:downloadtoken-detail', args=[self.download_token.guid]))
        self.assertEquals(response.status_code, status.HTTP_200_OK)
