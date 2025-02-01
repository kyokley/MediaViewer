import re

from django.db import models


class PersonManager(models.Manager):
    def create(self, *args, **kwargs):
        return self.get_or_create(*args, **kwargs)[0]

    def get_or_create(self, *args, **kwargs):
        # Remove anything appearing in parens
        kwargs["name"] = re.sub(r"\s+\(.*\)", "", kwargs["name"]).title()

        existing = self.filter(name=kwargs["name"]).first()

        if existing:
            return existing, False

        return super().get_or_create(*args, **kwargs)


class Person(models.Model):
    name = models.TextField(blank=False, null=False)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)

    objects = PersonManager()

    class Meta:
        abstract = True

    def __str__(self):
        return f"id: {self.id} n: {self.name}"
