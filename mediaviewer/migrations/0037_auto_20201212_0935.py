# Generated by Django 2.2.16 on 2020-12-12 15:35

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0036_donationsite"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usersettings",
            options={"verbose_name_plural": "User Settings"},
        ),
        migrations.AlterModelOptions(
            name="videoprogress",
            options={"verbose_name_plural": "Video Progress"},
        ),
    ]
