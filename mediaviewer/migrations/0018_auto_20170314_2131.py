# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-15 02:31
from __future__ import unicode_literals

from django.db import migrations


def regenerate_posterfiles(apps, schema_editor):
    PosterFile = apps.get_model('mediaviewer', 'PosterFile')
    PosterFile.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0017_actor_order'),
    ]

    operations = [
            migrations.RunPython(regenerate_posterfiles),
    ]
