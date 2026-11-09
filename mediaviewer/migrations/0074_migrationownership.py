from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mediaviewer", "0073_usersettings_captions_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="MigrationOwnership",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("run_id", models.UUIDField(blank=True, null=True, unique=True)),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "migration ownership", "verbose_name_plural": "migration ownership"},
        ),
        migrations.AddConstraint(
            model_name="migrationownership",
            constraint=models.CheckConstraint(condition=models.Q(id=1), name="migrationownership_singleton_pk"),
        ),
        migrations.RunPython(
            lambda apps, schema_editor: apps.get_model("mediaviewer", "MigrationOwnership").objects.using(schema_editor.connection.alias).get_or_create(pk=1),
            migrations.RunPython.noop,
        ),
    ]
