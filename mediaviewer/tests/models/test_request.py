import pytest

from datetime import timedelta

from django.contrib.auth.models import User
from mediaviewer.models.request import (
    Request,
    RequestVote,
)


@pytest.mark.django_db
class TestGetSupportingUsers:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user1 = User()
        self.user2 = User()
        self.user3 = User()

        self.user1.username = "user1"
        self.user2.username = "user2"
        self.user3.username = "user3"

        self.user1.save()
        self.user2.save()
        self.user3.save()

        self.request = Request.new("test request", self.user1)

    def test_(self):
        RequestVote.new(self.request, self.user1)
        RequestVote.new(self.request, self.user1)
        RequestVote.new(self.request, self.user3)

        expected = set([self.user1, self.user3])
        actual = set(self.request.getSupportingUsers())
        assert expected == actual


@pytest.mark.django_db
class TestCanVote:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user1 = User()
        self.user2 = User()
        self.user3 = User()

        self.user1.username = "user1"
        self.user2.username = "user2"
        self.user3.username = "user3"

        self.user1.save()
        self.user2.save()
        self.user3.save()

        self.request = Request.new("test request", self.user1)

    def test_voteAllowed(self):
        assert self.request.canVote(self.user1)

    def test_voteNotAllowed(self):
        RequestVote.new(self.request, self.user1)
        assert not self.request.canVote(self.user1)

    def test_voteAllowed2(self):
        req_vote = RequestVote.new(self.request, self.user1)
        req_vote.datecreated = req_vote.datecreated + timedelta(days=-1)
        req_vote.save()
        assert self.request.canVote(self.user1)


@pytest.mark.django_db
class TestRequestNew:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user1 = User()
        self.user2 = User()
        self.user3 = User()

        self.user1.username = "user1"
        self.user2.username = "user2"
        self.user3.username = "user3"

        self.user1.save()
        self.user2.save()
        self.user3.save()

        self.request = Request.new("this is a test", self.user1)

    def test_unique_request(self):
        new_obj = Request.new("new name", self.user1)
        assert new_obj != self.request

    def test_existing_request(self):
        new_obj = Request.new("This Is A Test", self.user1)
        assert new_obj == self.request
