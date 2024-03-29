# Generated by Django 3.2.20 on 2023-08-14 12:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0046_file__display_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="theme",
            field=models.CharField(
                choices=[("dark", "Dark"), ("light", "Light")],
                default="dark",
                max_length=32,
            ),
        ),
    ]
