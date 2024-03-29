# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-19 14:51
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0020_auto_20170421_0903"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="last_watched",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="mediaviewer.File",
            ),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="last_watched_dismissed",
            field=models.BooleanField(default=False),
        ),
    ]
