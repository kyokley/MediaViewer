import mock
import pytz
from datetime import datetime
from django.test import TestCase

#from django.contrib.auth.models import User
from mysite.settings import (TIME_ZONE,
                             )
from mediaviewer.models.loginevent import LoginEvent

@mock.patch('mediaviewer.models.loginevent.MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS', 3)
class TestNew(TestCase):
    def setUp(self):
        self.ref_time = datetime.now()
        self.objects_patcher = mock.patch('mediaviewer.models.loginevent.LoginEvent.objects')
        self.mock_objects = self.objects_patcher.start()
        self.mock_first = mock.MagicMock()
        self.mock_objects.order_by.return_value = self.mock_first
        self.addCleanup(self.objects_patcher.stop)

        self.save_patcher = mock.patch('mediaviewer.models.loginevent.LoginEvent.save')
        self.mock_save = self.save_patcher.start()
        self.addCleanup(self.save_patcher.stop)

        self.now_patcher = mock.patch('mediaviewer.models.loginevent.datetime')
        self.mock_now = self.now_patcher.start()
        self.mock_now.return_value = self.ref_time
        self.addCleanup(self.now_patcher.stop)

    def test_less_stored_events(self):
        self.mock_objects.count.return_value = 1
        event = LoginEvent.new(self.user)

        self.assertEqual(event.user, self.user)
        self.assertEqual(event.datecreated, self.ref_time)
        self.mock_save.assert_called_once_with()
        self.mock_now.assert_called_once_with(pytz.timezone(TIME_ZONE))
        self.assertFalse(self.mock_first.called)

    def test_more_stored_events(self):
        self.mock_objects.count.return_value = 3
        event = LoginEvent.new(self.user)

        self.assertEqual(event.user, self.user)
        self.assertEqual(event.datecreated, self.ref_time)
        self.mock_save.assert_called_once_with()
        self.mock_now.assert_called_once_with(pytz.timezone(TIME_ZONE))
        self.mock_first.delete.assert_called_once_with()
