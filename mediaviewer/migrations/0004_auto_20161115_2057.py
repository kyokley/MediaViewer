# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-16 02:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mediaviewer", "0003_merge_20161111_2120"),
    ]

    operations = [
        migrations.AlterField(
            model_name="request",
            name="datecreated",
            field=models.DateTimeField(auto_now_add=True, db_column="datecreated"),
        ),
        migrations.AlterField(
            model_name="request",
            name="dateedited",
            field=models.DateTimeField(auto_now=True, db_column="dateedited"),
        ),
        migrations.AlterField(
            model_name="requestvote",
            name="datecreated",
            field=models.DateTimeField(auto_now_add=True, db_column="datecreated"),
        ),
    ]
