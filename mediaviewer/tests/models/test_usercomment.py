import pytest

from mediaviewer.tests import helpers

from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.file import File
from mediaviewer.models.path import Path


@pytest.mark.django_db
class TestNew:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.path = Path.objects.create(
            localpathstr="local_path", remotepathstr="remote_path", is_movie=False
        )

        self.filename = "test_filename"
        self.file = File.objects.create(filename=self.filename, path=self.path)

        self.user = helpers.create_user(random=True)

    def test_new(self):
        uc = UserComment.new(self.file, self.user, "test_comment", False)
        print(uc)

        assert uc.file == self.file
        assert uc.user == self.user
        assert uc.comment == "test_comment"
        assert not uc.viewed
