import pytest
from django.contrib import admin

from mediaviewer.admin import MediaPathAdmin
from mediaviewer.models import MediaPath, Movie, TV


@pytest.mark.django_db
@pytest.mark.parametrize(("field_name", "media_model"), (("tv", TV), ("movie", Movie)))
def test_media_path_admin_media_choices_are_sorted_and_show_pk(field_name, media_model):
    media_objects = [
        media_model.objects.create(name="beta"),
        media_model.objects.create(name="Alpha"),
        media_model.objects.create(name="alpha"),
    ]
    model_admin = MediaPathAdmin(MediaPath, admin.site)
    field = model_admin.formfield_for_foreignkey(
        MediaPath._meta.get_field(field_name), request=None
    )

    choices = list(field.queryset)

    assert [media.pk for media in choices] == [
        media.pk
        for media in sorted(
            media_objects, key=lambda media: (media.name.lower(), media.pk)
        )
    ]
    assert [field.label_from_instance(media) for media in choices] == [
        f"<{media_model.__name__} pk:{media.pk} n:{media.name} f:False>"
        for media in choices
    ]
