# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-24 02:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='downloadtoken',
            name='waitertheme',
        ),
        migrations.RemoveField(
            model_name='usersettings',
            name='site_theme',
        ),
    ]