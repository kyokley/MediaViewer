from django.apps import AppConfig
from django.conf import settings


class MediaviewerConfig(AppConfig):
    name = "mediaviewer"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        if not settings.DEBUG:
            if not (settings.AUTH0_CLIENT_ID and
                    settings.AUTH0_CLIENT_SECRET and
                    settings.AUTH0_DOMAIN and
                    settings.AUTH0_LOGIN and
                    settings.AUTH0_PASSWORD):
                raise ValueError('Improper configuration')
