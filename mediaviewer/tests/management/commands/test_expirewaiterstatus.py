import pytest
from django.core.management import call_command

from mediaviewer.models import WaiterStatus


@pytest.mark.django_db
class TestCommand:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.command_name = "expirewaiterstatus"
        WaiterStatus.new(False, "Timeout")
        WaiterStatus.new(True, "")

    def test_two_statuses(self):
        call_command(self.command_name)

        assert WaiterStatus.objects.count() == 2

    def test_too_many_statuses(self):
        bulk_objs = []
        for i in range(100):
            bulk_objs.append(WaiterStatus(status=True))
        WaiterStatus.objects.bulk_create(bulk_objs)

        assert WaiterStatus.objects.count() == 102

        call_command(self.command_name)

        assert WaiterStatus.objects.count() == 10
