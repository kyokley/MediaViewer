from django.test import TestCase
from mediaviewer.views.home import (generateHeader,
                                    setSiteWideContext,
                                    getLastWaiterStatus,
                                    )
from mediaviewer.models.usersettings import FILENAME_SORT
from django.contrib.auth.models import User

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

        expected = {'loggedin': False,
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

        expected = {'loggedin': False,
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

        expected = {'loggedin': True,
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

@mock.patch('mediaviewer.views.home.HeaderHelper')
class TestGenerateHeaderUserIsStaff(TestCase):
    def setUp(self):
        self.request = mock.MagicMock()

        self.user = mock.create_autospec(User)
        self.user.is_staff = True
        self.user.is_authenticated.return_value = False

        self.request.user = self.user

    def test_home_is_active(self,
                            mock_HeaderHelper):
        mock_headers = mock.MagicMock()
        mock_HeaderHelper.return_value = mock_headers
        page = 'home'
        generateHeader(page, self.request)

        mock_headers.activeHomePage.assert_called_once_with()
        self.assertFalse(mock_headers.homePage.called)
        mock_headers.moviesPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeMoviesPage.called)
        mock_headers.tvshowsPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeTvshowsPage.called)
        mock_headers.requestsPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeRequestsPage.called)

    def test_movies_is_active(self,
                              mock_HeaderHelper):
        mock_headers = mock.MagicMock()
        mock_HeaderHelper.return_value = mock_headers
        page = 'movies'
        generateHeader(page, self.request)

        mock_headers.homePage.assert_called_once_with()
        self.assertFalse(mock_headers.activeHomePage.called)
        mock_headers.activeMoviesPage.assert_called_once_with()
        self.assertFalse(mock_headers.moviesPage.called)
        mock_headers.tvshowsPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeTvshowsPage.called)
        mock_headers.requestsPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeRequestsPage.called)

    def test_tvshows_is_active(self,
                               mock_HeaderHelper):
        mock_headers = mock.MagicMock()
        mock_HeaderHelper.return_value = mock_headers
        page = 'tvshows'
        generateHeader(page, self.request)

        mock_headers.homePage.assert_called_once_with()
        self.assertFalse(mock_headers.activeHomePage.called)
        mock_headers.moviesPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeMoviesPage.called)
        mock_headers.activeTvshowsPage.assert_called_once_with()
        self.assertFalse(mock_headers.tvshowsPage.called)
        mock_headers.requestsPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeRequestsPage.called)

    def test_requests_is_active(self,
                                mock_HeaderHelper):
        mock_headers = mock.MagicMock()
        mock_HeaderHelper.return_value = mock_headers
        page = 'requests'
        generateHeader(page, self.request)

        mock_headers.homePage.assert_called_once_with()
        self.assertFalse(mock_headers.activeHomePage.called)
        mock_headers.moviesPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeMoviesPage.called)
        mock_headers.tvshowsPage.assert_called_once_with()
        self.assertFalse(mock_headers.activeTvshowsPage.called)
        mock_headers.activeRequestsPage.assert_called_once_with()
        self.assertFalse(mock_headers.requestsPage.called)
