import pytest

from mediaviewer.models.waiterstatus import WaiterStatus


@pytest.mark.django_db
class TestNew:
    def test_new(self):
        ws = WaiterStatus.new(True, "reason")

        assert ws.status is True
        assert ws.failureReason == "reason"


@pytest.mark.django_db
class TestGetLastStatus:
    def test_getLastStatus(self):
        self.ws1 = WaiterStatus.new(False, "reason1")
        self.ws2 = WaiterStatus.new(False, "reason2")

        ws = WaiterStatus.getLastStatus()
        assert ws == self.ws2

    def test_empty(self):
        ws = WaiterStatus.getLastStatus()
        assert ws is None
