# Generated by Django 2.1.5 on 2019-07-14 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mediaviewer", "0034_migrate_paths"),
    ]

    operations = [
        migrations.AddField(
            model_name="path",
            name="finished",
            field=models.BooleanField(default=False),
        ),
    ]
