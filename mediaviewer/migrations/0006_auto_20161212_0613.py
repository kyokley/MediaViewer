# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-12 12:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0005_auto_20161127_1008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercomment',
            name='datecreated',
            field=models.DateTimeField(auto_now_add=True, db_column=b'datecreated'),
        ),
        migrations.AlterField(
            model_name='usercomment',
            name='dateedited',
            field=models.DateTimeField(auto_now=True, db_column=b'dateedited'),
        ),
    ]
