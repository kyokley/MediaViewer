from django.test import TestCase
from mediaviewer.models.path import Path
from mediaviewer.models.file import File
from mediaviewer.models.mediagenre import MediaGenre

class TestGetMediaGenres(TestCase):
    def setUp(self):
        self.movie_path = Path()
        self.movie_path.is_movie = True
        self.movie_path.save()

        self.tv_path = Path()
        self.tv_path.is_movie = False
        self.tv_path.save()

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

        self.tv_file1 = File()
        self.tv_file1.filename = 'This.is.a.tv.file1'
        self.tv_file1.path = self.tv_path
        self.tv_file1.save()

        self.tv_file2 = File()
        self.tv_file2.filename = 'This.is.a.tv.file2'
        self.tv_file2.path = self.tv_path
        self.tv_file2.save()

        self.tv_file3 = File()
        self.tv_file3.filename = 'This.is.a.tv.file3'
        self.tv_file3.path = self.tv_path
        self.tv_file3.save()

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
