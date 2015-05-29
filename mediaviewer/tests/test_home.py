from django.test import TestCase
from mediaviewer.views.home import (generateHeader,
                                    home,
                                    setSiteWideContext,
                                    getLastWaiterStatus,
                                    )
from mediaviewer.models.usersettings import DEFAULT_SITE_THEME, FILENAME_SORT
from django.contrib.auth.models import User

# These imports are required to allow tests to run
from mediaviewer.models.path import Path
from mediaviewer.models.datatransmission import DataTransmission

import mock
from mock import call

@mock.patch('mediaviewer.views.home.Message.add_message')
@mock.patch('mediaviewer.views.home.Message.getMessagesForUser')
@mock.patch('mediaviewer.views.home.getLastWaiterStatus')
class TestSetSiteWideContext(TestCase):
    def setUp(self):
        self.request = mock.MagicMock()

        self.user = mock.create_autospec(User)

        self.request.user = self.user

    def test_is_staff_not_logged_in(self,
                                    mock_getLastWaiterStatus,
                                    mock_getMessageForUser,
                                    mock_add_message):
        self.user.is_staff = True
        self.user.is_authenticated.return_value = False

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'site_theme': DEFAULT_SITE_THEME,
                    'loggedin': False,
                    'is_staff': 'true'}
        self.assertEquals(call(expected), mock_getLastWaiterStatus.call_args)
        self.assertFalse(mock_getMessageForUser.called)
        self.assertFalse(mock_add_message.called)

    def test_not_staff_not_logged_in(self,
                                    mock_getLastWaiterStatus,
                                    mock_getMessageForUser,
                                    mock_add_message):
        self.user.is_staff = False
        self.user.is_authenticated.return_value = False

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'site_theme': DEFAULT_SITE_THEME,
                    'loggedin': False,
                    'is_staff': 'false'}
        self.assertEquals(call(expected), mock_getLastWaiterStatus.call_args)
        self.assertFalse(mock_getMessageForUser.called)
        self.assertFalse(mock_add_message.called)

    def test_is_staff_is_logged_in(self,
                                    mock_getLastWaiterStatus,
                                    mock_getMessageForUser,
                                    mock_add_message):
        self.user.is_staff = True
        self.user.is_authenticated.return_value = True
        self.user.settings.return_value = None

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'site_theme': DEFAULT_SITE_THEME,
                    'loggedin': True,
                    'is_staff': 'true',
                    'default_sort': FILENAME_SORT,
                    'user': self.user}
        self.assertEquals(call(expected), mock_getLastWaiterStatus.call_args)
        self.assertFalse(mock_getMessageForUser.called)
        self.assertFalse(mock_add_message.called)

class TestGetLastWaiterStatus(TestCase):
    @mock.patch('mediaviewer.views.home.WaiterStatus')
    def test_getLastWaiterStatus(self, mock_WaiterStatus):
        context = {}
        mock_lastStatus = mock.MagicMock()
        mock_lastStatus.status = True
        mock_lastStatus.failureReason = 'test'
        mock_WaiterStatus.getLastStatus.return_value = mock_lastStatus

        getLastWaiterStatus(context)

        self.assertTrue(context['waiterstatus'])
        self.assertEquals('test', context['waiterfailurereason'])

class TestGenerateHeaderUserIsStaff(TestCase):
    def setUp(self):
        self.request = mock.MagicMock()

        self.user = mock.create_autospec(User)
        self.user.is_staff = True
        self.user.is_authenticated.return_value = False

        self.request.user = self.user

    def _removeWhiteSpaceFromTuple(self, inTup):
        
        firstString = inTup[0].replace(' ', '')
        firstString = firstString.replace('\n', '')

        secondString = inTup[1].replace(' ', '')
        secondString = secondString.replace('\n', '')
        return (firstString, secondString)

    def test_generate_home_header(self):
        page = 'home'
        headers = generateHeader(page, self.request)
        expected = ('\n                <li class="active"><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        <li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>\n        <li><a href="/mediaviewer/userusage/">User Data Usage</a></li>\n        <li><a href="/mediaviewer/errors/display/50/">Errors</a></li>\n        ')
        expected = self._removeWhiteSpaceFromTuple(expected)
        headers = self._removeWhiteSpaceFromTuple(headers)
        self.assertEqual(headers, expected)

    def test_generate_movie_header(self):
        page = 'movies'
        headers = generateHeader(page, self.request)
        expected = ('\n                <li><a href="/mediaviewer/">Home</a></li>\n                <li class="active"><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        <li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>\n        <li><a href="/mediaviewer/userusage/">User Data Usage</a></li>\n        <li><a href="/mediaviewer/errors/display/50/">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)

    def test_generate_tvshows_header(self):
        page = 'tvshows'
        headers = generateHeader(page, self.request)
        expected = ('\n                <li><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li class="active"><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        <li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>\n        <li><a href="/mediaviewer/userusage/">User Data Usage</a></li>\n        <li><a href="/mediaviewer/errors/display/50/">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)

    def test_generate_requests_header(self):
        page = 'requests'
        headers = generateHeader(page, self.request)
        expected = ('\n                <li><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li class="active"><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        <li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>\n        <li><a href="/mediaviewer/userusage/">User Data Usage</a></li>\n        <li><a href="/mediaviewer/errors/display/50/">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)

    def test_generate_datausage_header(self):
        page = 'datausage'
        headers = generateHeader(page, self.request)
        expected = ('\n                <li><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        <li class="active"><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>\n        <li><a href="/mediaviewer/userusage/">User Data Usage</a></li>\n        <li><a href="/mediaviewer/errors/display/50/">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)

    def test_generate_errors_header(self):
        page = 'errors'
        headers = generateHeader(page, self.request)
        expected = ('\n                <li><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        <li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>\n        <li><a href="/mediaviewer/userusage/">User Data Usage</a></li>\n        <li class="active"><a href="/mediaviewer/errors/display/50/">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)

    def test_generate_header_user_not_staff(self):
        page = 'home'
        self.request.user = mock.MagicMock()
        self.request.user.is_staff = False
        headers = generateHeader(page, self.request)
        expected = ('\n                <li class="active"><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        \n        \n        <li class="disabled"><a href="#">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)
