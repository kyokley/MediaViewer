# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-04 16:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0012_auto_20170121_2207"),
    ]

    operations = [
        migrations.DeleteModel(
            name="MediaGenre",
        )
    ]
