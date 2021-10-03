import pytest
from mediaviewer.models.actor import Actor


@pytest.mark.django_db
class TestCreate:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.test_name = 'test_name'

        assert not Actor.objects.exists()

    @pytest.mark.parametrize('expected_order', (None, 10))
    def test_create(self, expected_order):
        Actor.objects.create(name=self.test_name,
                             order=expected_order)

        new_actor = Actor.objects.get()
        assert new_actor.name == 'Test_Name'
        assert new_actor.order == expected_order
