# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-20 02:30
from __future__ import unicode_literals

from django.db import migrations

# Normally, we would use apps.get_model to get at the class here
# However, I'm only interested in running the class method in this migration
from mediaviewer.models.mediagenre import MediaGenre

def generate_initial_mediagenre_data(apps, schema_editor):
    #MediaGenre.regenerateAllGenreData()
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0010_mediagenre'),
    ]

    operations = [
        migrations.RunPython(generate_initial_mediagenre_data)
    ]
