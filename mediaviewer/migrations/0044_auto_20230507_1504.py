# Generated by Django 3.2.19 on 2023-05-07 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0043_alter_usersettings_last_watched'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usersettings',
            old_name='can_download',
            new_name='_can_download',
        ),
        migrations.AddField(
            model_name='usersettings',
            name='verified',
            field=models.BooleanField(default=True),
        ),
    ]