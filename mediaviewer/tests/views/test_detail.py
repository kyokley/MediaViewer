import mock

from django.test import TestCase
from django.http import HttpRequest

from mediaviewer.views.detail import (
        ajaxsuperviewed,
        filesdetail,
        )
from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import (
        UserSettings,
        LOCAL_IP,
        BANGUP_IP,
        )
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.usercomment import UserComment


class TestAjaxSuperViewed(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch(
                'mediaviewer.views.detail.DownloadToken.objects.filter',
                autospec=True)
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.HttpResponse_patcher = mock.patch(
                'mediaviewer.views.detail.HttpResponse',
                autospec=True)
        self.mock_HttpResponse = self.HttpResponse_patcher.start()
        self.addCleanup(self.HttpResponse_patcher.stop)

        self.dumps_patcher = mock.patch('mediaviewer.views.detail.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.token = mock.MagicMock(DownloadToken)
        self.token.isvalid = True

        self.mock_filter.return_value.first.return_value = self.token

        self.request = mock.MagicMock()
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

    def test_no_token(self):
        self.mock_filter.return_value.first.return_value = None

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': 'Token is invalid',
                                                 'guid': 'test_guid',
                                                 'viewed': True})
        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                status=400,
                content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.assertFalse(self.token.file.markFileViewed.called)

    def test_token_invalid(self):
        self.token.isvalid = False

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': 'Token is invalid',
                                                 'guid': 'test_guid',
                                                 'viewed': True})
        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                status=400,
                content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.assertFalse(self.token.file.markFileViewed.called)

    def test_not_viewed(self):
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'False'}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': '',
                                                 'guid': 'test_guid',
                                                 'viewed': False})
        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                status=200,
                content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.token.file.markFileViewed.assert_called_once_with(
                self.token.user,
                False)

    def test_viewed(self):
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxsuperviewed(self.request)

        self.assertEquals(expected, actual)

        self.mock_dumps.assert_called_once_with({'errmsg': '',
                                                 'guid': 'test_guid',
                                                 'viewed': True})
        self.mock_HttpResponse.assert_called_once_with(
                self.mock_dumps.return_value,
                status=200,
                content_type='application/json')
        self.mock_filter.assert_called_once_with(guid='test_guid')
        self.mock_filter.return_value.first.assert_called_once_with()

        self.token.file.markFileViewed.assert_called_once_with(
                self.token.user,
                True)


class TestAjaxSuperViewedResponseStatusCode(TestCase):
    def setUp(self):
        self.filter_patcher = mock.patch(
                'mediaviewer.views.detail.DownloadToken.objects.filter',
                autospec=True)
        self.mock_filter = self.filter_patcher.start()
        self.addCleanup(self.filter_patcher.stop)

        self.dumps_patcher = mock.patch('mediaviewer.views.detail.json.dumps')
        self.mock_dumps = self.dumps_patcher.start()
        self.addCleanup(self.dumps_patcher.stop)

        self.token = mock.MagicMock(DownloadToken)
        self.token.isvalid = True

        self.mock_filter.return_value.first.return_value = self.token

        self.request = mock.MagicMock()
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

    def test_success(self):
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

        resp = ajaxsuperviewed(self.request)
        self.assertEquals(resp.status_code, 200)

    def test_failure(self):
        self.token.isvalid = False
        self.request.POST = {'guid': 'test_guid',
                             'viewed': 'True'}

        resp = ajaxsuperviewed(self.request)
        self.assertEquals(resp.status_code, 400)


class TestFilesDetail(TestCase):
    def setUp(self):
        setSiteWideContext_patcher = mock.patch(
                'mediaviewer.views.detail.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        render_patcher = mock.patch(
                'mediaviewer.views.detail.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

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

        self.user = UserSettings.new('test_user', 'a@b.com')
        self.user.settings().force_password_change = False

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_no_comment(self):
        expected_context = {
                'file': self.tv_file,
                'posterfile': self.tv_file.posterfile,
                'comment': '',
                'skip': self.tv_file.skip,
                'finished': self.tv_file.finished,
                'LOCAL_IP': LOCAL_IP,
                'BANGUP_IP': BANGUP_IP,
                'viewed': False,
                'can_download': True,
                'file_size': None,
                'active_page': 'filesdetail',
                'title': 'Tv Local Path',
                }
        expected = self.mock_render.return_value
        actual = filesdetail(self.request, self.tv_file.id)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/filesdetail.html',
                expected_context)

    def test_comment(self):
        usercomment = UserComment()
        usercomment.file = self.tv_file
        usercomment.user = self.user
        usercomment.viewed = True
        usercomment.comment = 'test_comment'
        usercomment.save()

        expected_context = {
                'file': self.tv_file,
                'posterfile': self.tv_file.posterfile,
                'comment': 'test_comment',
                'skip': self.tv_file.skip,
                'finished': self.tv_file.finished,
                'LOCAL_IP': LOCAL_IP,
                'BANGUP_IP': BANGUP_IP,
                'viewed': True,
                'can_download': True,
                'file_size': None,
                'active_page': 'filesdetail',
                'title': 'Tv Local Path',
                }
        expected = self.mock_render.return_value
        actual = filesdetail(self.request, self.tv_file.id)

        self.assertEqual(expected, actual)
        self.mock_setSiteWideContext.assert_called_once_with(
                expected_context,
                self.request)
        self.mock_render.assert_called_once_with(
                self.request,
                'mediaviewer/filesdetail.html',
                expected_context)
