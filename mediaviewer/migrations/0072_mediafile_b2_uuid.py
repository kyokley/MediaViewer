from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0071_mediafile_subtitle_files_mediapath_subtitle_files")
    ]

    operations = [
        migrations.AddField(
            model_name="mediafile",
            name="b2_uuid",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
    ]
