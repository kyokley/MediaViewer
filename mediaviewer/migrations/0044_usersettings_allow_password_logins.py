# Generated by Django 3.2.20 on 2023-07-28 14:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0043_alter_usersettings_last_watched"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="allow_password_logins",
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
