import mock

from django.test import TestCase
from django.http import HttpRequest

from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.views.home import (
    home,
    ajaxrunscraper,
)

from mediaviewer.tests.helpers import create_user


class TestHome(TestCase):
    def setUp(self):
        most_recent_files_patcher = mock.patch(
            'mediaviewer.views.home.File.most_recent_files')
        self.mock_most_recent_files = most_recent_files_patcher.start()
        self.addCleanup(most_recent_files_patcher.stop)

        setSiteWideContext_patcher = mock.patch(
            'mediaviewer.views.home.setSiteWideContext')
        self.mock_setSiteWideContext = setSiteWideContext_patcher.start()
        self.addCleanup(setSiteWideContext_patcher.stop)

        render_patcher = mock.patch(
            'mediaviewer.views.home.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        self.change_password_patcher = mock.patch(
            'mediaviewer.views.password_reset.change_password')
        self.mock_change_password = self.change_password_patcher.start()

        self.user = create_user()

        self.tv_path = Path.objects.create(localpathstr='tv.local.path',
                                           remotepathstr='tv.remote.path',
                                           is_movie=False)
        self.tv_file = File.objects.create(filename='tv.file', path=self.tv_path)

        self.mock_most_recent_files.return_value = [self.tv_file]

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_with_greeting(self):
        SiteGreeting.new(
            self.user,
            'test_greeting')

        expected_context = {
            'greeting': 'test_greeting',
            'active_page': 'home',
            'files': [self.tv_file],
            'title': 'Home',
        }

        expected = self.mock_render.return_value
        actual = home(self.request)

        self.assertEqual(expected, actual)
        self.mock_most_recent_files.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context,
            self.request,
            includeMessages=True)
        self.mock_render.assert_called_once_with(
            self.request,
            'mediaviewer/home.html',
            expected_context)

    def test_no_greeting(self):
        expected_context = {
            'greeting': 'Check out the new downloads!',
            'active_page': 'home',
            'files': [self.tv_file],
            'title': 'Home',
        }

        expected = self.mock_render.return_value
        actual = home(self.request)

        self.assertEqual(expected, actual)
        self.mock_most_recent_files.assert_called_once_with()
        self.mock_setSiteWideContext.assert_called_once_with(
            expected_context,
            self.request,
            includeMessages=True)
        self.mock_render.assert_called_once_with(
            self.request,
            'mediaviewer/home.html',
            expected_context)

    def test_force_password_change(self):
        settings = self.user.settings()
        settings.force_password_change = True
        settings.save()

        expected = self.mock_change_password.return_value
        actual = home(self.request)

        self.assertEqual(expected, actual)
        self.mock_change_password.assert_called_once_with()


class TestAjaxRunScraper(TestCase):
    def setUp(self):
        inferAllScrapers_patcher = mock.patch(
            'mediaviewer.views.home.File.inferAllScrapers')
        self.mock_inferAllScrapers = inferAllScrapers_patcher.start()
        self.addCleanup(inferAllScrapers_patcher.stop)

        dumps_patcher = mock.patch(
            'mediaviewer.views.home.json.dumps')
        self.mock_dumps = dumps_patcher.start()
        self.addCleanup(dumps_patcher.stop)

        HttpResponse_patcher = mock.patch(
            'mediaviewer.views.home.HttpResponse')
        self.mock_HttpResponse = HttpResponse_patcher.start()
        self.addCleanup(HttpResponse_patcher.stop)

        self.user = create_user()

        self.request = mock.MagicMock(HttpRequest)
        self.request.user = self.user

    def test_not_staff(self):
        expected_response = {'errmsg': ''}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxrunscraper(self.request)

        self.assertEqual(expected, actual)
        self.assertFalse(self.mock_inferAllScrapers.called)
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value,
            content_type='application/javascript')

    def test_staff(self):
        self.user.is_staff = True

        expected_response = {'errmsg': ''}

        expected = self.mock_HttpResponse.return_value
        actual = ajaxrunscraper(self.request)

        self.assertEqual(expected, actual)
        self.mock_inferAllScrapers.assert_called_once_with()
        self.mock_dumps.assert_called_once_with(expected_response)
        self.mock_HttpResponse.assert_called_once_with(
            self.mock_dumps.return_value,
            content_type='application/javascript')
