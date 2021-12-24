# Generated by Django 2.2.25 on 2021-12-24 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0039_auto_20210214_1317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='finished',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='skip',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='path',
            name='server',
            field=models.TextField(default='127.0.0.1'),
        ),
        migrations.AlterField(
            model_name='path',
            name='skip',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
