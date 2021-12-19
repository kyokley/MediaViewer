import pytest
from faker import Faker

from mediaviewer.models.path import Path
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile


fake = Faker()


def _counter_gen():
    count = 1
    while True:
        yield count
        count += 1


_count = _counter_gen()


@pytest.fixture()
def create_path():
    def _create_path(localpathstr=None,
                     remotepathstr=None,
                     skip=False,
                     is_movie=False,
                     ):
        if localpathstr is None:
            localpathstr = f'/path/to/localpath_{next(_count)}'

        if remotepathstr is None:
            remotepathstr = f'/path/to/remotepath_{next(_count)}'

        return Path.objects.create(localpathstr=localpathstr,
                                   remotepathstr=remotepathstr,
                                   skip=skip,
                                   is_movie=is_movie)
    return _create_path


@pytest.fixture()
def create_file(create_path):
    def _create_file(path=None,
                     filename=None,
                     skip=False,
                     finished=True,
                     size=100,
                     streamable=True):
        if path is None:
            path = create_path()

        if filename is None:
            filename = f'test_filename{next(_count)}'

        return File.objects.create(path=path,
                                   filename=filename,
                                   skip=skip,
                                   finished=finished,
                                   size=size,
                                   streamable=streamable)
    return _create_file


@pytest.fixture()
def create_poster_file():
    def _create_poster_file(file=None,
                            path=None,
                            genres=None,
                            plot=None,
                            extendedplot=None):
        if file is None and path is None or (file and path):
            raise Exception('Either file or path must be defined but not both')

        if genres is None:
            genres = []

        if plot is None:
            plot = fake.sentence()

        if extendedplot is None:
            extendedplot = fake.paragraph()

        poster_file = PosterFile.objects.create(
            file=file,
            path=path,
            plot=plot,
            extendedplot=extendedplot,
        )

        for genre in genres:
            poster_file.genres.add(genre)

        return poster_file
    return _create_poster_file
