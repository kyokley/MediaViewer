# Generated by Django 2.2.18 on 2021-02-13 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mediaviewer", "0037_auto_20201212_0935"),
    ]

    operations = [
        migrations.AlterField(
            model_name="posterfile",
            name="actors",
            field=models.ManyToManyField(blank=True, to="mediaviewer.Actor"),
        ),
        migrations.AlterField(
            model_name="posterfile",
            name="directors",
            field=models.ManyToManyField(blank=True, to="mediaviewer.Director"),
        ),
        migrations.AlterField(
            model_name="posterfile",
            name="genres",
            field=models.ManyToManyField(blank=True, to="mediaviewer.Genre"),
        ),
        migrations.AlterField(
            model_name="posterfile",
            name="writers",
            field=models.ManyToManyField(blank=True, to="mediaviewer.Writer"),
        ),
    ]
