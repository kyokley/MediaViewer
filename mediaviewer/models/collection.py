from django.db import models


class Collection(models.Model):
    name = models.CharField(max_length=255,
                            null=False,
                            unique=True,
                            )

    def __str__(self):
        return f'<Collection "{self.name}">'

    def __repr__(self):
        return str(self)
