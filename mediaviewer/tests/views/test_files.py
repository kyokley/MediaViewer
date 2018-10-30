import mock

from django.test import TestCase
from django.http import HttpRequest, Http404

from django.contrib.auth.models import (Group,
                                        AnonymousUser,
                                        )
from mediaviewer.models.usersettings import (
        UserSettings,
        )

from mediaviewer.models.file import File
from mediaviewer.models.path import Path

from mediaviewer.views.files import files


class TestFiles(TestCase):
    def setUp(self):
        self.tv_path = Path.new('tv.local.path',
                                'tv.remote.path',
                                is_movie=False)
        self.tv_path.tvdb_id = None

        self.tv_file = File.new('tv.file', self.tv_path)
        self.tv_file.override_filename = 'test str'
        self.tv_file.override_season = '3'
        self.tv_file.override_episode = '5'

        mv_group = Group(name='MediaViewer')
        mv_group.save()

        self.user = UserSettings.new(
                'test_user',
                'a@b.com',
                send_email=False)
        self.user.settings().force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user
