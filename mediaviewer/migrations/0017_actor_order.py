# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-12 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0016_posterfile_tmdb_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="actor",
            name="order",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
