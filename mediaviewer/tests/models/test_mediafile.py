import pytest

from mediaviewer.models import MediaFile, Poster


@pytest.mark.django_db
@pytest.mark.parametrize("use_tv", (True, False))
def test_delete(create_movie_media_file,
                create_tv_media_file,
                use_tv):
    if use_tv:
        mf = create_tv_media_file()
    else:
        mf = create_movie_media_file()

    Poster.objects.from_ref_obj(mf)

    MediaFile.objects.all().delete()
    assert not MediaFile.objects.filter(pk=mf.id).exists()
