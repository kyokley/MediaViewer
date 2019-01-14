import mock
import pytz
from datetime import datetime
from django.test import TestCase

from django.conf import settings
from mediaviewer.tests import helpers
from mediaviewer.models.loginevent import LoginEvent


class TestNew(TestCase):
    def setUp(self):
        self.ref_time = datetime.now(pytz.timezone(settings.TIME_ZONE))
        self.objects_patcher = mock.patch(
                'mediaviewer.models.loginevent.LoginEvent.objects')
        self.mock_objects = self.objects_patcher.start()
        self.mock_ordered_query = mock.MagicMock()
        self.mock_first = mock.MagicMock()
        self.mock_ordered_query.first.return_value = self.mock_first
        self.mock_objects.order_by.return_value = self.mock_ordered_query
        self.addCleanup(self.objects_patcher.stop)

        self.save_patcher = mock.patch(
                'mediaviewer.models.loginevent.LoginEvent.save')
        self.mock_save = self.save_patcher.start()
        self.addCleanup(self.save_patcher.stop)

        self.datetime_patcher = mock.patch(
                'mediaviewer.models.loginevent.datetime')
        self.mock_datetime = self.datetime_patcher.start()
        self.mock_datetime.now.return_value = self.ref_time
        self.addCleanup(self.datetime_patcher.stop)

        self.user = helpers.create_user()

    def test_less_stored_events(self):
        self.mock_objects.count.return_value = 1
        event = LoginEvent.new(self.user)

        self.assertEqual(event.user, self.user)
        self.assertEqual(event.datecreated, self.ref_time)
        self.mock_save.assert_called_once_with()
        self.assertFalse(self.mock_first.called)

    def test_more_stored_events(self):
        self.mock_objects.count.return_value = (
            settings.MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS + 1)
        event = LoginEvent.new(self.user)

        self.assertEqual(event.user, self.user)
        self.assertEqual(event.datecreated, self.ref_time)
        self.mock_save.assert_called_once_with()
        self.mock_first.delete.assert_called_once_with()
