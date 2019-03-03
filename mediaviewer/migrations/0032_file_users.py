# Generated by Django 2.1.5 on 2019-03-03 02:03

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mediaviewer', '0031_auto_20190113_0949'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='users',
            field=models.ManyToManyField(through='mediaviewer.UserComment', to=settings.AUTH_USER_MODEL),
        ),
    ]
