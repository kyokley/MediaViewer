# Generated by Django 4.2.15 on 2024-11-09 14:05

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0063_poster_release_date"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usersettings",
            name="ip_format",
        ),
    ]
