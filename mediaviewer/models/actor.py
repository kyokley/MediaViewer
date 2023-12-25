from django.db import models

from mediaviewer.models.person import Person


class Actor(Person):
    order = models.IntegerField(blank=True, null=True)

    class Meta:
        app_label = "mediaviewer"
        db_table = "actor"

    @classmethod
    def new(cls, name, order=None):
        new_obj = super().new(name)
        new_obj.order = order
        new_obj.save()
        return new_obj
