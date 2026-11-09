from django.conf import settings
from django.db import models


class MigrationOwnership(models.Model):
    """Durable singleton lock for remote media migration runs."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    run_id = models.UUIDField(null=True, blank=True, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "migration ownership"
        verbose_name_plural = "migration ownership"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="migrationownership_singleton_pk")]

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
