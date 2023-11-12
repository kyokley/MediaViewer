import pytest
import shutil
from faker import Faker

from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.utils import getSomewhatUniqueID

from mediaviewer.models import Movie, TV

DEFAULT_USERNAME = "test_user"
DEFAULT_EMAIL = "asdf@example.com"

fake = Faker()


def _counter_gen():
    count = 1
    while True:
        yield count
        count += 1


_count = _counter_gen()


@pytest.fixture
def temp_dir(tmp_path):
    dir = tmp_path
    yield dir
    if dir.exists():
        shutil.rmtree(dir)


@pytest.fixture
def create_movie(temp_dir):
    def _create_movie(
        name=None,
        finished=False,
        path=None,
        poster=None
    ):
        if name is None:
            name = f'Movie {next(_count)}'

        if not path:
            path = temp_dir

        movie = Movie.objects.create(
            name=name,
            finished=finished,
            path=path,
            poster=poster)
        return movie
    return _create_movie


@pytest.fixture
def create_tv(temp_dir):
    def _create_tv(
        name=None,
        finished=False,
        path=None,
        poster=None
    ):
        if name is None:
            name = f'TV {next(_count)}'

        if not path:
            path = temp_dir

        return TV.objects.create(
            name=name,
            finished=finished,
            path=path,
            poster=poster)
    return _create_tv


@pytest.fixture
def create_tv_media_file(create_tv):
    def _create_tv_media_file(tv=None,
                              filename=None,
                              display_name=None):
        if tv is None:
            tv = create_tv()

        if filename is None:
            filename = f'foo{next(_count)}.mp4'

        if display_name is None:
            display_name = filename

        return tv.add_episode(filename, display_name)
    return _create_tv_media_file


@pytest.fixture
def create_user():
    def _create_user(
        username=None,
        email=None,
        group_name="MediaViewer",
        send_email=False,
        force_password_change=False,
        is_staff=False,
    ):
        mv_group, _ = Group.objects.get_or_create(name=group_name)

        if not username:
            username = f'{DEFAULT_USERNAME}{next(_count)}'

        if not email:
            email = f'asdf{next(_count)}@example.com'

        user = UserSettings.new(
            username, email, send_email=send_email, group=mv_group, is_staff=is_staff
        )
        settings = user.settings()
        settings.force_password_change = force_password_change
        return user
    return _create_user
