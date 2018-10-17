from django.test import TestCase

from mediaviewer.views.views_utils import (setSiteWideContext,
                                           getLastWaiterStatus,
                                           )
from mediaviewer.models.usersettings import FILENAME_SORT
from mediaviewer.models.message import Message
from django.contrib.auth.models import User

import mock
from mock import call


class TestSetSiteWideContext(TestCase):
    def setUp(self):
        self.add_message_patcher = mock.patch(
                'mediaviewer.views.views_utils.Message.add_message')
        self.mock_add_message = self.add_message_patcher.start()
        self.addCleanup(self.add_message_patcher.stop)

        self.getMessagesForUser_patcher = mock.patch(
                'mediaviewer.views.views_utils.Message.getMessagesForUser')
        self.mock_getMessagesForUser = self.getMessagesForUser_patcher.start()
        self.addCleanup(self.getMessagesForUser_patcher.stop)

        self.getLastWaiterStatus_patcher = mock.patch(
                'mediaviewer.views.views_utils.getLastWaiterStatus')
        self.mock_getLastWaiterStatus = (
                self.getLastWaiterStatus_patcher.start())
        self.addCleanup(self.getLastWaiterStatus_patcher.stop)

        self.get_movie_genres_patcher = mock.patch(
                'mediaviewer.views.views_utils.File.get_movie_genres')
        self.mock_get_movie_genres = self.get_movie_genres_patcher.start()
        self.addCleanup(self.get_movie_genres_patcher.stop)

        self.get_tv_genres_patcher = mock.patch(
                'mediaviewer.views.views_utils.Path.get_tv_genres')
        self.mock_get_tv_genres = self.get_tv_genres_patcher.start()
        self.addCleanup(self.get_tv_genres_patcher.stop)

        self.first_message = mock.MagicMock(Message)
        self.second_message = mock.MagicMock(Message)

        self.mock_getMessagesForUser.side_effect = [(self.first_message,),
                                                    (self.second_message,)
                                                    ]

        self.request = mock.MagicMock()
        self.user = mock.create_autospec(User)
        self.request.user = self.user

    def test_is_staff_not_logged_in(self):
        self.user.is_staff = True
        self.user.is_authenticated.return_value = False

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'loggedin': False,
                    'is_staff': 'true'}
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        self.assertFalse(self.mock_getMessagesForUser.called)
        self.assertFalse(self.mock_add_message.called)

    def test_not_staff_not_logged_in(self):
        self.user.is_staff = False
        self.user.is_authenticated.return_value = False

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'loggedin': False,
                    'is_staff': 'false'}
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        self.assertFalse(self.mock_getMessagesForUser.called)
        self.assertFalse(self.mock_add_message.called)

    def test_is_staff_is_logged_in(self):
        self.user.is_staff = True
        self.user.is_authenticated.return_value = True
        self.user.settings.return_value = None

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {'loggedin': True,
                    'is_staff': 'true',
                    'default_sort': FILENAME_SORT,
                    'user': self.user,
                    'movie_genres': self.mock_get_movie_genres.return_value,
                    'tv_genres': self.mock_get_tv_genres.return_value}
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        self.assertFalse(self.mock_getMessagesForUser.called)
        self.assertFalse(self.mock_add_message.called)

    def test_includeMessages_not_staff(self):
        self.user.is_staff = False
        self.user.is_authenticated.return_value = True
        self.user.settings.return_value = None

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=True)

        expected = {'loggedin': True,
                    'is_staff': 'false',
                    'default_sort': FILENAME_SORT,
                    'user': self.user,
                    'movie_genres': self.mock_get_movie_genres.return_value,
                    'tv_genres': self.mock_get_tv_genres.return_value}
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        self.mock_add_message.assert_has_calls(
                [call(self.request,
                      self.first_message.level,
                      self.first_message.body,
                      extra_tags=str(self.first_message.id)),
                 call(self.request,
                      self.second_message.level,
                      self.second_message.body,
                      extra_tags=str(self.second_message.id) + ' last_watched')
                 ])


class TestGetLastWaiterStatus(TestCase):
    def setUp(self):
        self.WaiterStatus_patcher = mock.patch(
                'mediaviewer.views.views_utils.WaiterStatus')
        self.mock_WaiterStatus = self.WaiterStatus_patcher.start()
        self.addCleanup(self.WaiterStatus_patcher.stop)

    def test_getLastWaiterStatus(self):
        context = {}
        mock_lastStatus = mock.MagicMock()
        mock_lastStatus.status = True
        mock_lastStatus.failureReason = 'test'
        self.mock_WaiterStatus.getLastStatus.return_value = mock_lastStatus

        getLastWaiterStatus(context)

        self.assertTrue(context['waiterstatus'])
        self.assertEquals('test', context['waiterfailurereason'])
