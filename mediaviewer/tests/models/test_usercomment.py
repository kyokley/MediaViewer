from django.test import TestCase

from mediaviewer.tests import helpers

from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.file import File
from mediaviewer.models.path import Path


class TestNew(TestCase):
    def setUp(self):
        self.path = Path.new('local_path',
                             'remote_path',
                             False)

        self.filename = 'test_filename'
        self.file = File.new(self.filename,
                             self.path)

        self.user = helpers.create_user(random=True)

    def test_new(self):
        uc = UserComment.new(
                self.file,
                self.user,
                'test_comment',
                False)
        print(uc)

        self.assertEqual(uc.file, self.file)
        self.assertEqual(uc.user, self.user)
        self.assertEqual(uc.comment, 'test_comment')
        self.assertEqual(uc.viewed, False)
