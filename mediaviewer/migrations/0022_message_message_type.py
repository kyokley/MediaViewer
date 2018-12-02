# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-19 15:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0021_auto_20170819_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='message_type',
            field=models.CharField(blank=True, choices=[(b'regular', b'Regular'), (b'last_watched', b'Last Watched')], default=b'regular', max_length=15),
        ),
    ]
