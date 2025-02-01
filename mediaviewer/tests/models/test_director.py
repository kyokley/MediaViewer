import pytest

from mediaviewer.models.director import Director


@pytest.mark.django_db
class TestCreate:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_name = "test_name"

        assert not Director.objects.exists()

    def test_create(self):
        Director.objects.create(name=self.test_name)

        new_director = Director.objects.get()
        assert new_director.name == "Test_Name"
