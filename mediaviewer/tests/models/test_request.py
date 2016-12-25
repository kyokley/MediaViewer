from django.test import TestCase

from django.contrib.auth.models import User
from mediaviewer.models.request import (Request,
                                        RequestVote,
                                        )

class TestGetSupportingUsers(TestCase):
    def setUp(self):
        self.user1 = User()
        self.user2 = User()
        self.user3 = User()

        self.user1.username = 'user1'
        self.user2.username = 'user2'
        self.user3.username = 'user3'

        self.user1.save()
        self.user2.save()
        self.user3.save()

        self.request = Request.new('test request',
                                   self.user1)

    def test_(self):
        RequestVote.new(self.request, self.user1)
        RequestVote.new(self.request, self.user1)
        RequestVote.new(self.request, self.user3)

        expected = set([self.user1, self.user3])
        actual = set(self.request.getSupportingUsers())
        self.assertEqual(expected, actual)

class TestCanVote(TestCase):
    def setUp(self):
        self.user1 = User()
        self.user2 = User()
        self.user3 = User()

        self.user1.username = 'user1'
        self.user2.username = 'user2'
        self.user3.username = 'user3'

        self.user1.save()
        self.user2.save()
        self.user3.save()

        self.request = Request.new('test request',
                                   self.user1)

    def test_voteAllowed(self):
        self.assertTrue(self.request.canVote(self.user1))

    def test_voteNotAllowed(self):
        RequestVote.new(self.request, self.user1)
        self.assertFalse(self.request.canVote(self.user1))
