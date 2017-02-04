import mock
from django.test import TestCase

from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.file import File
from mediaviewer.models.path import Path

class TestAssignDataToPoster(TestCase):
    def setUp(self):
        genres_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.genres', mock.MagicMock())
        genres_patcher.start()
        self.addCleanup(genres_patcher.stop)
        actors_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.actors', mock.MagicMock())
        actors_patcher.start()
        self.addCleanup(actors_patcher.stop)
        writers_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.writers', mock.MagicMock())
        writers_patcher.start()
        self.addCleanup(writers_patcher.stop)
        directors_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.directors', mock.MagicMock())
        directors_patcher.start()
        self.addCleanup(directors_patcher.stop)

        genre_obj_patcher = mock.patch('mediaviewer.models.posterfile.Genre.new', mock.MagicMock(side_effect=lambda x: x))
        genre_obj_patcher.start()
        self.addCleanup(genre_obj_patcher.stop)

        actor_obj_patcher = mock.patch('mediaviewer.models.posterfile.Actor.new', mock.MagicMock(side_effect=lambda x: x))
        actor_obj_patcher.start()
        self.addCleanup(actor_obj_patcher.stop)

        writer_obj_patcher = mock.patch('mediaviewer.models.posterfile.Writer.new', mock.MagicMock(side_effect=lambda x: x))
        writer_obj_patcher.start()
        self.addCleanup(writer_obj_patcher.stop)

        director_obj_patcher = mock.patch('mediaviewer.models.posterfile.Director.new', mock.MagicMock(side_effect=lambda x: x))
        director_obj_patcher.start()
        self.addCleanup(director_obj_patcher.stop)

        self.poster = PosterFile()
        self.poster.plot = None
        self.poster.rating = None
        self.poster.rated = None
        self.poster.extendedplot = None

    def test_all_data(self):
        data = {'Plot': 'plot',
                'Genre': 'Action, Drama, Crime',
                'Actors': 'Meridith Steele, Margy Marks, Merna Rutledge, Krissy Cole, Cammie Howell',
                'Writer': 'Eleonore Carter, Kym Hodge',
                'Director': 'Neda English, Gwyn Carson, Alica Ellis',
                'imdbRating': 'imdb_rating',
                'Rated': 'rated',
                }

        self.poster._assignDataToPoster(data)

        self.assertEquals(self.poster.plot, 'plot')
        self.poster.genres.add.assert_any_call('Action')
        self.poster.genres.add.assert_any_call('Drama')
        self.poster.genres.add.assert_any_call('Crime')
        self.poster.actors.add.assert_any_call('Meridith Steele')
        self.poster.actors.add.assert_any_call('Margy Marks')
        self.poster.actors.add.assert_any_call('Merna Rutledge')
        self.poster.actors.add.assert_any_call('Krissy Cole')
        self.poster.actors.add.assert_any_call('Cammie Howell')
        self.poster.writers.add.assert_any_call('Eleonore Carter')
        self.poster.writers.add.assert_any_call('Kym Hodge')
        self.poster.directors.add.assert_any_call('Neda English')
        self.poster.directors.add.assert_any_call('Gwyn Carson')
        self.poster.directors.add.assert_any_call('Alica Ellis')
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

        self.poster._assignDataToPoster(data, onlyExtendedPlot=True)
        self.assertEquals(self.poster.plot, None)
        self.assertFalse(self.poster.genres.add.called)
        self.assertFalse(self.poster.actors.add.called)
        self.assertFalse(self.poster.writers.add.called)
        self.assertFalse(self.poster.directors.add.called)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, 'plot')

    def test_undefined(self):
        data = {'Plot': 'undefined',
                'Genre': 'undefined',
                'Actors': 'undefined',
                'Writer': 'undefined',
                'Director': 'undefined',
                'imdbRating': 'undefined',
                'Rated': 'undefined',
                }

        self.poster._assignDataToPoster(data, onlyExtendedPlot=False)
        self.assertEquals(self.poster.plot, None)
        self.assertFalse(self.poster.genres.add.called)
        self.assertFalse(self.poster.actors.add.called)
        self.assertFalse(self.poster.writers.add.called)
        self.assertFalse(self.poster.directors.add.called)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, None)

    def test_undefined_onlyExtendedPlot(self):
        data = {'Plot': 'undefined',
                'Genre': 'undefined',
                'Actors': 'undefined',
                'Writer': 'undefined',
                'Director': 'undefined',
                'imdbRating': 'undefined',
                'Rated': 'undefined',
                }

        self.poster._assignDataToPoster(data, onlyExtendedPlot=True)
        self.assertEquals(self.poster.plot, None)
        self.assertFalse(self.poster.genres.add.called)
        self.assertFalse(self.poster.actors.add.called)
        self.assertFalse(self.poster.writers.add.called)
        self.assertFalse(self.poster.directors.add.called)
        self.assertEquals(self.poster.rating, None)
        self.assertEquals(self.poster.rated, None)
        self.assertEquals(self.poster.extendedplot, None)

class TestNew(TestCase):
    def setUp(self):
        objects_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile.objects')
        self.mock_objects = objects_patcher.start()
        self.addCleanup(objects_patcher.stop)

        downloadPosterData_patcher = mock.patch('mediaviewer.models.posterfile.PosterFile._downloadPosterData')
        self.mock_downloadPosterData = downloadPosterData_patcher.start()
        self.addCleanup(downloadPosterData_patcher.stop)

        self.path = Path.new('local.path',
                             'remote.path',
                             is_movie=False)
        self.movie_path = Path.new('movie.local.path',
                                   'movie.remote.path',
                                   is_movie=True)
        self.file = File.new('new.file.mp4',
                             self.movie_path)

        self.mock_objects.filter.return_value.first.return_value = None


    def test_no_file_no_path(self):
        self.assertRaises(ValueError,
                          PosterFile.new)

    def test_file(self):
        new_obj = PosterFile.new(file=self.file)

        self.assertEqual(new_obj.file, self.file)
        self.assertEqual(new_obj.path, None)
        self.mock_downloadPosterData.assert_called_once_with()

    def test_path(self):
        new_obj = PosterFile.new(path=self.path)

        self.assertEqual(new_obj.file, None)
        self.assertEqual(new_obj.path, self.path)
        self.mock_downloadPosterData.assert_called_once_with()

    def test_existing_for_file(self):
        self.mock_objects.filter.return_value.first.return_value = 'existing_obj'

        existing = PosterFile.new(file=self.file)
        self.assertEqual(existing, 'existing_obj')
        self.assertFalse(self.mock_downloadPosterData.called)

    def test_existing_for_path(self):
        self.mock_objects.filter.return_value.first.return_value = 'existing_obj'

        existing = PosterFile.new(path=self.path)
        self.assertEqual(existing, 'existing_obj')
        self.assertFalse(self.mock_downloadPosterData.called)
