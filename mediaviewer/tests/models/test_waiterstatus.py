from django.test import TestCase

from mediaviewer.models.waiterstatus import WaiterStatus


class TestNew(TestCase):
    def test_new(self):
        ws = WaiterStatus.new(True, "reason")

        self.assertEqual(ws.status, True)
        self.assertEqual(ws.failureReason, "reason")


class TestGetLastStatus(TestCase):
    def setUp(self):
        self.ws1 = WaiterStatus.new(False, "reason1")
        self.ws2 = WaiterStatus.new(False, "reason2")

    def test_getLastStatus(self):
        ws = WaiterStatus.getLastStatus()
        self.assertEqual(ws, self.ws2)
