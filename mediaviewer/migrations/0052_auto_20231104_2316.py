# Generated by Django 3.2.20 on 2023-11-05 04:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0051_auto_20231104_0848'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mediafile',
            old_name='poster',
            new_name='_poster',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='_search_terms',
        ),
        migrations.RemoveField(
            model_name='tv',
            name='_search_terms',
        ),
    ]
