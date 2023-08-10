# Generated by Django 3.2.20 on 2023-08-10 20:24

from django.db import migrations


def forward(apps, schema_editor):
    File = apps.get_model('mediaviewer', 'File')

    count = File.objects.count()
    for idx, file in enumerate(File.objects.all()):
        file.displayName()
        print(f'{idx}/{count}')


class Migration(migrations.Migration):

    dependencies = [
        ('mediaviewer', '0046_file__display_name'),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
