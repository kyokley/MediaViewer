import re
from django.db import models

class Person(models.Model):
    name = models.TextField(blank=False,
                            null=False)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'id: %s n: %s' % (self.id, self.name)

    @classmethod
    def new(cls, name):
        # Remove anything appearing in parens
        name = re.sub('\s+\(.*\)', '', name)

        existing = cls.objects.filter(name=name.title()).first()

        if existing:
            return existing

        new_obj = cls()
        new_obj.name = name.title()
        new_obj.save()
        return new_obj

