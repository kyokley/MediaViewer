# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-19 15:26
from __future__ import unicode_literals

from django.db import migrations
from mediaviewer.models.file import File
from mediaviewer.models.path import Path


def regenerate_posterfiles(apps, schema_editor):
    PosterFile = apps.get_model('mediaviewer', 'PosterFile')
    PosterFile.objects.all().delete()

    File.populate_all_posterfiles()
    Path.populate_all_posterfiles()

class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0014_auto_20170204_1047'),
    ]

    operations = [
            migrations.RunPython(regenerate_posterfiles),
    ]
