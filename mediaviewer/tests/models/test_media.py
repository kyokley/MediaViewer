import pytest

from mediaviewer.models import TV, Movie, Poster


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


@pytest.mark.django_db
@pytest.mark.parametrize("media_model", (TV, Movie))
def test_media_str_and_repr_include_primary_key(media_model):
    media = media_model.objects.create(name="Name", finished=False)

    expected = f"<{media_model.__name__} pk:{media.pk} n:Name f:False>"

    assert str(media) == expected
    assert repr(media) == expected
