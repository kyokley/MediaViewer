# Generated by Django 3.2.20 on 2023-08-10 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0045_remove_sitegreeting_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='_display_name',
            field=models.TextField(blank=True, default=''),
        ),
    ]
