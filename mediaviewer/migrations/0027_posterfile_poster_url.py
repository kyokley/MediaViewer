# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-23 02:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mediaviewer", "0026_remove_usersettings_auto_download"),
    ]

    operations = [
        migrations.AddField(
            model_name="posterfile",
            name="poster_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
