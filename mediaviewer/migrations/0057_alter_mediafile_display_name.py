# Generated by Django 3.2.25 on 2024-03-31 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0056_auto_20240324_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediafile',
            name='display_name',
            field=models.CharField(blank=True, max_length=256),
        ),
    ]
