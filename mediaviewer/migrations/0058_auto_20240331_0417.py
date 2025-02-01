# Generated by Django 3.2.25 on 2024-03-31 09:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0057_alter_mediafile_display_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="poster",
            name="actors",
            field=models.ManyToManyField(
                blank=True, editable=False, to="mediaviewer.Actor"
            ),
        ),
        migrations.AlterField(
            model_name="poster",
            name="directors",
            field=models.ManyToManyField(
                blank=True, editable=False, to="mediaviewer.Director"
            ),
        ),
        migrations.AlterField(
            model_name="poster",
            name="genres",
            field=models.ManyToManyField(
                blank=True, editable=False, to="mediaviewer.Genre"
            ),
        ),
        migrations.AlterField(
            model_name="poster",
            name="writers",
            field=models.ManyToManyField(
                blank=True, editable=False, to="mediaviewer.Writer"
            ),
        ),
    ]
