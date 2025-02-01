import mock
import pytest
from django.contrib.auth.models import User
from mock import call

from mediaviewer.models import Collection
from mediaviewer.models.message import Message
from mediaviewer.models.usersettings import FILENAME_SORT
from mediaviewer.views.views_utils import getLastWaiterStatus, setSiteWideContext


@pytest.mark.django_db
class TestSetSiteWideContext:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker, create_collection):
        create_collection()

        self.mock_add_message = mocker.patch(
            "mediaviewer.views.views_utils.Message.add_message"
        )

        self.mock_getMessagesForUser = mocker.patch(
            "mediaviewer.views.views_utils.Message.getMessagesForUser"
        )

        self.mock_getLastWaiterStatus = mocker.patch(
            "mediaviewer.views.views_utils.getLastWaiterStatus"
        )

        self.mock_get_movie_genres = mocker.patch(
            "mediaviewer.views.views_utils.Genre.objects.get_movie_genres"
        )

        self.mock_get_tv_genres = mocker.patch(
            "mediaviewer.views.views_utils.Genre.objects.get_tv_genres"
        )

        self.first_message = mock.MagicMock(Message)
        self.second_message = mock.MagicMock(Message)

        self.mock_getMessagesForUser.side_effect = [
            (self.first_message,),
            (self.second_message,),
        ]

        self.request = mock.MagicMock()
        self.user = mock.create_autospec(User)
        self.request.user = self.user

    def test_is_staff_not_logged_in(self):
        self.user.is_staff = True
        self.user.is_authenticated = False

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {
            "loggedin": False,
            "is_staff": "true",
            "donation_site_name": "",
            "donation_site_url": "",
            "theme": mock.ANY,
        }
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        assert not self.mock_getMessagesForUser.called
        assert not self.mock_add_message.called

    def test_not_staff_not_logged_in(self):
        self.user.is_staff = False
        self.user.is_authenticated = False

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {
            "loggedin": False,
            "is_staff": "false",
            "donation_site_name": "",
            "donation_site_url": "",
            "theme": mock.ANY,
        }
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        assert not self.mock_getMessagesForUser.called
        assert not self.mock_add_message.called

    def test_is_staff_is_logged_in(self):
        self.user.is_staff = True
        self.user.is_authenticated = True
        self.user.settings.return_value = None

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=False)

        expected = {
            "theme": "dark",
            "loggedin": True,
            "user": self.user,
            "default_sort": FILENAME_SORT,
            "movie_genres": self.mock_get_movie_genres.return_value,
            "tv_genres": self.mock_get_tv_genres.return_value,
            "collections": list(Collection.objects.order_by("name")),
            "is_staff": "true",
            "donation_site_name": "",
            "donation_site_url": "",
        }
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        assert not self.mock_getMessagesForUser.called
        assert not self.mock_add_message.called

    def test_includeMessages_not_staff(self):
        self.user.is_staff = False
        self.user.is_authenticated = True
        self.user.settings.return_value = None

        context = dict()
        setSiteWideContext(context, self.request, includeMessages=True)

        expected = {
            "loggedin": True,
            "is_staff": "false",
            "default_sort": FILENAME_SORT,
            "donation_site_name": "",
            "donation_site_url": "",
            "user": self.user,
            "movie_genres": self.mock_get_movie_genres.return_value,
            "tv_genres": self.mock_get_tv_genres.return_value,
            "theme": "dark",
            "collections": list(Collection.objects.order_by("name")),
        }
        self.mock_getLastWaiterStatus.assert_called_once_with(expected)
        self.mock_add_message.assert_has_calls(
            [
                call(
                    self.request,
                    self.first_message.level,
                    self.first_message.body,
                    extra_tags=str(self.first_message.id),
                ),
                call(
                    self.request,
                    self.second_message.level,
                    self.second_message.body,
                    extra_tags=str(self.second_message.id) + " last_watched",
                ),
            ]
        )


class TestGetLastWaiterStatus:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_WaiterStatus = mocker.patch(
            "mediaviewer.views.views_utils.WaiterStatus"
        )

    def test_getLastWaiterStatus(self):
        context = {}
        mock_lastStatus = mock.MagicMock()
        mock_lastStatus.status = True
        mock_lastStatus.failureReason = "test"
        self.mock_WaiterStatus.getLastStatus.return_value = mock_lastStatus

        getLastWaiterStatus(context)

        assert context["waiterstatus"]
        assert "test" == context["waiterfailurereason"]
