# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-22 04:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0011_auto_20170119_2030"),
    ]

    operations = [
        migrations.AlterField(
            model_name="posterfile",
            name="datecreated",
            field=models.DateTimeField(auto_now_add=True, db_column="datecreated"),
        ),
        migrations.AlterField(
            model_name="posterfile",
            name="dateedited",
            field=models.DateTimeField(auto_now=True, db_column="dateedited"),
        ),
    ]
