from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("mediaviewer", "0074_migrationownership")]

    operations = [
        migrations.AddField(
            model_name="mediapath",
            name="migration_source",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="migration_target",
                to="mediaviewer.mediapath",
            ),
        ),
    ]
