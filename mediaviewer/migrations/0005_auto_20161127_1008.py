# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-27 16:08
from __future__ import unicode_literals

from django.db import migrations, models

def rename_filename(apps, schema_editor):
    VideoProgress = apps.get_model('mediaviewer', 'VideoProgress')
    for vp in VideoProgress.objects.all():
        vp.hashed_filename = vp.filename
        vp.save()

class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0004_auto_20161115_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoprogress',
            name='hashed_filename',
            field=models.TextField(db_column=b'hashedfilename', null=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='videoprogress',
            name='filename',
            field=models.TextField(db_column=b'filename', null=True),
        ),
        migrations.RunPython(rename_filename),
        migrations.AlterField(
            model_name='videoprogress',
            name='hashed_filename',
            field=models.TextField(db_column=b'hashedfilename', null=False),
        ),
    ]
