import pytest
from mediaviewer.models.writer import Writer


@pytest.mark.django_db
class TestCreate:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_name = "test_name"

        assert not Writer.objects.exists()

    def test_create(self):
        Writer.objects.create(name=self.test_name)

        new_writer = Writer.objects.get()
        assert new_writer.name == "Test_Name"
