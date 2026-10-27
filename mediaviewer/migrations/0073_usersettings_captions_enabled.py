from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mediaviewer", "0072_mediafile_b2_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="captions_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
