import pytest

from mediaviewer.models import Poster, TV, Movie


@pytest.mark.django_db
class TestDelete:
    @pytest.fixture(autouse=True)
    def setUp(self, create_tv, create_movie):
        self.tv = create_tv()
        self.movie = create_movie()

    @pytest.mark.parametrize("use_tv", (True, False))
    def test_delete_obj(self, use_tv):
        if use_tv:
            self.media = self.tv
        else:
            self.media = self.movie

        Poster.objects.from_ref_obj(self.media)

        self.media.delete()

        with pytest.raises(self.media.DoesNotExist):
            self.media.refresh_from_db()

    @pytest.mark.parametrize("use_tv", (True, False))
    def test_delete_qs(self, use_tv):
        if use_tv:
            media = self.tv
            media_class = TV
        else:
            media = self.movie
            media_class = Movie

        Poster.objects.from_ref_obj(media)

        media_class.objects.delete()

        with pytest.raises(media.DoesNotExist):
            media.refresh_from_db()
