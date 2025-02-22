import shutil
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from faker import Faker

from mediaviewer.models import (
    TV,
    MediaFile,
    MediaPath,
    Movie,
    Collection,
    DownloadToken,
)
from mediaviewer.models.usersettings import UserSettings

DEFAULT_USERNAME = "test_user"
DEFAULT_EMAIL = "asdf@example.com"

DEFAULT_USERNAME = "test_user"
DEFAULT_EMAIL = "a@b.com"

fake = Faker()


def _counter_gen():
    count = 1
    while True:
        yield count
        count += 1


_count = _counter_gen()


@pytest.fixture(autouse=True)
def mock_requests(mocker):
    mock = mocker.patch("mediaviewer.models.tvdbconfiguration.requests.get")
    mock.side_effect = Exception("Failing external requests on purpose")


@pytest.fixture
def temp_dir(tmp_path):
    base_dir = Path(tmp_path)

    def _temp_dir():
        dir = base_dir / str(next(_count))
        return dir

    yield _temp_dir
    if base_dir.exists():
        shutil.rmtree(base_dir)


@pytest.fixture
def create_media_path(temp_dir):
    def _create_media_path(path=None, tv=None, movie=None):
        if tv is None and movie is None:
            raise ValueError("Either tv or movie must be provided")

        if not path:
            path = temp_dir()

        mp = MediaPath.objects.create(_path=path, tv=tv, movie=movie)
        return mp

    return _create_media_path


@pytest.fixture
def create_movie(create_media_path):
    def _create_movie(
        name=None,
        finished=False,
        poster=None,
        hide=False,
    ):
        if name is None:
            name = f"Movie {next(_count)}"

        movie = Movie.objects.create(
            name=name,
            finished=finished,
            _poster=poster,
            hide=hide,
        )

        create_media_path(movie=movie)

        return movie

    return _create_movie


@pytest.fixture
def create_tv(create_media_path):
    def _create_tv(
        name=None,
        finished=False,
        poster=None,
        hide=False,
    ):
        if name is None:
            name = f"TV {next(_count)}"

        tv = TV.objects.create(
            name=name,
            finished=finished,
            _poster=poster,
            hide=hide,
        )

        create_media_path(tv=tv)
        return tv

    return _create_tv


@pytest.fixture
def create_tv_media_file(create_tv):
    def _create_tv_media_file(tv=None, filename=None, display_name=None):
        if tv is None:
            tv = create_tv()

        if filename is None:
            filename = f"foo{next(_count)}.mp4"

        if display_name is None:
            display_name = filename

        return tv.add_episode(filename, display_name)

    return _create_tv_media_file


@pytest.fixture
def create_movie_media_file(create_movie):
    def _create_movie_media_file(movie=None, filename=None, display_name=None):
        if movie is None:
            movie = create_movie()

        if filename is None:
            filename = f"foo{next(_count)}.mp4"

        if display_name is None:
            display_name = filename

        return MediaFile.objects.create(
            media_path=movie.media_path, filename=filename, display_name=display_name
        )

    return _create_movie_media_file


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
            username = f"{DEFAULT_USERNAME}{next(_count)}"

        if not email:
            email = f"asdf{next(_count)}@example.com"

        user = UserSettings.new(
            username, email, send_email=send_email, group=mv_group, is_staff=is_staff
        )
        settings = user.settings()
        settings.force_password_change = force_password_change
        return user

    return _create_user


@pytest.fixture
def create_collection():
    def _create_collection(
        name=None,
    ):
        if name is None:
            name = f"Collection {next(_count)}"
        return Collection.objects.create(name=name)

    return _create_collection


@pytest.fixture
def create_download_token(create_user, create_tv_media_file):
    def _create_download_token(user=None, media_file=None):
        if user is None:
            user = create_user()

        if media_file is None:
            media_file = create_tv_media_file()

        dt = DownloadToken.objects.from_media_file(user, media_file)
        return dt

    return _create_download_token
