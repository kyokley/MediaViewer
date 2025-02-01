from datetime import datetime

import mock
import pytest
import pytz
from django.conf import settings
from mediaviewer.models.loginevent import LoginEvent


@pytest.mark.django_db
class TestNew:
    @pytest.fixture(autouse=True)
    def setUp(self, create_user, mocker):
        self.ref_time = datetime.now(pytz.timezone(settings.TIME_ZONE))
        self.mock_objects = mocker.patch(
            "mediaviewer.models.loginevent.LoginEvent.objects"
        )
        self.mock_ordered_query = mock.MagicMock()
        self.mock_first = mock.MagicMock()
        self.mock_ordered_query.first.return_value = self.mock_first
        self.mock_objects.order_by.return_value = self.mock_ordered_query

        self.mock_save = mocker.patch("mediaviewer.models.loginevent.LoginEvent.save")

        self.mock_datetime = mocker.patch("mediaviewer.models.loginevent.datetime")
        self.mock_datetime.now.return_value = self.ref_time

        self.user = create_user()

    def test_less_stored_events(self):
        self.mock_objects.count.return_value = 1
        event = LoginEvent.new(self.user)

        assert event.user == self.user
        assert event.datecreated == self.ref_time
        self.mock_save.assert_called_once_with()
        assert not self.mock_first.called

    def test_more_stored_events(self):
        self.mock_objects.count.return_value = (
            settings.MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS + 1
        )
        event = LoginEvent.new(self.user)

        assert event.user == self.user
        assert event.datecreated == self.ref_time
        self.mock_save.assert_called_once_with()
        self.mock_first.delete.assert_called_once_with()
