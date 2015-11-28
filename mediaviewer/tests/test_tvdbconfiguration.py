import mock

from django.test import TestCase
from mediaviewer.models.tvdbconfiguration import assignDataToPoster
from mediaviewer.models.posterfile import PosterFile

class TestAssignDataToPoster(TestCase):
    def setUp(self):
        self.poster = mock.create_autospec(PosterFile)
        self.poster.plot = None
        self.poster.genre = None
        self.poster.actors = None
        self.poster.writer = None
        self.poster.director = None
        self.poster.rating = None
        self.poster.rated = None
        self.poster.extendedplot = None

    def test_all_data(self):
        data = {'Plot': 'plot',
                'Genre': 'genre',
                'Actors': 'actors',
                'Writer': 'writer',
                'Director': 'director',
                'imdbRating': 'imdb_rating',
                'Rated': 'rated',
                }

        assignDataToPoster(data, self.poster)
        self.assertEquals(self.poster.plot, 'plot')
        self.assertEquals(self.poster.genre, 'genre')
        self.assertEquals(self.poster.actors, 'actors')
        self.assertEquals(self.poster.writer, 'writer')
        self.assertEquals(self.poster.director, 'director')
        self.assertEquals(self.poster.rating, 'imdb_rating')
        self.assertEquals(self.poster.rated, 'rated')
        self.assertEquals(self.poster.extendedplot, None)

    def test_onlyExtendedPlot(self):
        data = {'Plot': 'plot',
                'Genre': 'genre',
                'Actors': 'actors',
                'Writer': 'writer',
                'Director': 'director',
                'imdbRating': 'imdb_rating',
                'Rated': 'rated',
                }

        assignDataToPoster(data, self.poster, onlyExtendedPlot=True)
        self.assertEquals(self.poster.plot, None)
        self.assertEquals(self.poster.genre, None)
        self.assertEquals(self.poster.actors, None)
        self.assertEquals(self.poster.writer, None)
        self.assertEquals(self.poster.director, None)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, 'plot')

    def test_foundNone(self):
        data = {'Plot': 'plot',
                'Genre': 'genre',
                'Actors': 'actors',
                'Writer': 'writer',
                'Director': 'director',
                'imdbRating': 'imdb_rating',
                'Rated': 'rated',
                }

        assignDataToPoster(data, self.poster, foundNone=True)
        self.assertEquals(self.poster.plot, 'Plot not found')
        self.assertEquals(self.poster.genre, 'Genre not found')
        self.assertEquals(self.poster.actors, 'Actors not found')
        self.assertEquals(self.poster.writer, 'Writer not found')
        self.assertEquals(self.poster.director, 'Director not found')
        self.assertEquals(self.poster.extendedplot, 'Extended plot not found')
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)

    def test_undefined(self):
        data = {'Plot': 'undefined',
                'Genre': 'undefined',
                'Actors': 'undefined',
                'Writer': 'undefined',
                'Director': 'undefined',
                'imdbRating': 'undefined',
                'Rated': 'undefined',
                }

        assignDataToPoster(data, self.poster)
        self.assertEquals(self.poster.plot, 'Plot not found')
        self.assertEquals(self.poster.genre, 'Genre not found')
        self.assertEquals(self.poster.actors, 'Actors not found')
        self.assertEquals(self.poster.writer, 'Writer not found')
        self.assertEquals(self.poster.director, 'Director not found')
        self.assertEquals(self.poster.extendedplot, None)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)

    def test_undefined_onlyExtendedPlot(self):
        data = {'Plot': 'undefined',
                'Genre': 'undefined',
                'Actors': 'undefined',
                'Writer': 'undefined',
                'Director': 'undefined',
                'imdbRating': 'undefined',
                'Rated': 'undefined',
                }

        assignDataToPoster(data, self.poster, onlyExtendedPlot=True)
        self.assertEquals(self.poster.plot, None)
        self.assertEquals(self.poster.genre, None)
        self.assertEquals(self.poster.actors, None)
        self.assertEquals(self.poster.writer, None)
        self.assertEquals(self.poster.director, None)
        self.assertEquals(self.poster.extendedplot, 'Plot not found')
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
