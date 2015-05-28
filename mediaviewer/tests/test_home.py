from django.test import TestCase
from mediaviewer.views.home import (generateHeader,
                                    home,
                                    setSiteWideContext,
                                    )
from django.contrib.auth.models import User

# These imports are required to allow tests to run
from mediaviewer.models.path import Path
from mediaviewer.models.datatransmission import DataTransmission

import mock
from mock import call

class MockUser(object):
    def __init__(self,
                 is_authenticated=False,
                 is_staff=False):
        self._is_authenticated = is_authenticated
        self._is_staff = is_staff

    def is_authenticated(self):
        return self._is_authenticated

    @property
    def is_staff(self):
        return self._is_staff

class MockRequest(object):
    def __init__(self, user=None):
        if user:
            self.user = user
        else:
            self.user = MockUser()

class TestHomeView(TestCase):
    def setUp(self):
        self.request = mock.MagicMock()

        self.user = mock.create_autospec(User)
        self.user.is_staff = True
        self.user.is_authenticated.return_value = False

        self.request.user = self.user

    @mock.patch('mediaviewer.views.home.getLastWaiterStatus')
    def test_home_view(self, mock_getLastWaiterStatus):
        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'site_theme': 'default',
                    'loggedin': False,
                    'is_staff': 'true'}
        self.assertEquals(call(expected), mock_getLastWaiterStatus.call_args)

class TestGenerateHeaderUserIsStaff(TestCase):
    def setUp(self):
        self.user = MockUser(is_staff=True)
        self.request = MockRequest(user=self.user)

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
        self.request.user = MockUser(is_staff=False)
        headers = generateHeader(page, self.request)
        expected = ('\n                <li class="active"><a href="/mediaviewer/">Home</a></li>\n                <li><a href="/mediaviewer/movies/display/0/">Movies</a></li>\n                <li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>\n                <li><a href="/mediaviewer/requests/">Requests</a></li>\n    ', '\n        \n        \n        <li class="disabled"><a href="#">Errors</a></li>\n        ')
        self.assertEqual(headers, expected)
