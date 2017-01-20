from django.test import TestCase
from mediaviewer.models.path import Path
from mediaviewer.models.file import File
from mediaviewer.models.mediagenre import MediaGenre

class TestGetMediaGenres(TestCase):
    def setUp(self):
        self.movie_path = Path.new('local.movie',
                                   'local.movie',
                                   is_movie=True)

        self.tv_path = Path.new('local.tv',
                                'local.tv',
                                is_movie=False)

        self.movie_file1 = File.new('This.is.a.movie.file1',
                                    self.movie_path)
        MediaGenre.new('Action',
                       file=self.movie_file1)

        self.movie_file2 = File.new('This.is.a.movie.file2',
                                    self.movie_path)
        MediaGenre.new('Action',
                       file=self.movie_file2)
        MediaGenre.new('History',
                       file=self.movie_file2)

        self.movie_file3 = File.new('This.is.a.movie.file3',
                                    self.movie_path)
        MediaGenre.new('Action',
                       file=self.movie_file3)
        MediaGenre.new('History',
                       file=self.movie_file3)
        MediaGenre.new('Adventure',
                       file=self.movie_file3)

        self.tv_file1 = File.new('This.is.a.tv.file1',
                                 self.tv_path)

        self.tv_file2 = File.new('This.is.a.tv.file2',
                                 self.tv_path)

        self.tv_file3 = File.new('This.is.a.tv.file3',
                                 self.tv_path)

        MediaGenre.new('Crime',
                       path=self.tv_path)
        MediaGenre.new('Thriller',
                       path=self.tv_path)
        MediaGenre.new('Biography',
                       path=self.tv_path)

    def test_get_movie_genres(self):
        expected = ['Action',
                    'Adventure',
                    'History']
        genres = MediaGenre.get_movie_genres()
        actual = [genre.genre for genre in genres]
        self.assertEqual(expected, actual)

    def test_get_tv_genres(self):
        expected = ['Biography',
                    'Crime',
                    'Thriller']
        genres = MediaGenre.get_tv_genres()
        actual = [genre.genre for genre in genres]
        self.assertEqual(expected, actual)
