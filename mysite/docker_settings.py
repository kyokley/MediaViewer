import os

from pathlib import Path
from mysite.settings import *  # noqa

USE_SILK = DEBUG = os.environ.get("MV_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "mediaviewer"]

ADMINS = (("Docker", "docker@example.com"),)
MANAGERS = ADMINS

DATABASES = {
    # Testing settings!!!
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("MV_NAME", "postgres"),
        "USER": os.environ.get("MV_USER", os.environ.get("USER")),
        "PASSWORD": os.environ.get("MV_PASSWORD", "postgres"),
        "HOST": os.environ.get("MV_HOST", "postgres"),
        "PORT": os.environ.get("MV_PORT", ""),  # Set to empty string for default.
    },
}

if DEBUG:
    INSTALLED_APPS += (
        "silk",
        "debug_toolbar",
    )

    MIDDLEWARE = ("silk.middleware.SilkyMiddleware",) + MIDDLEWARE

    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

MEDIA_ROOT = (
    Path(os.environ["MV_MEDIA_ROOT"])
    if os.environ.get("MV_MEDIA_ROOT")
    else Path(__file__).parent.parent / "media"
)

STATIC_ROOT = (
    Path(os.environ["MV_STATIC_DIR"])
    if os.environ.get("MV_STATIC_DIR")
    else Path(__file__).parent.parent / "static"
)
# static_file_path.mkdir(exist_ok=True)


WAITER_STATUS_URL = "http://mediawaiter:5000/waiter/status"
WAITER_HEAD = "http://"
WAITER_IP_FORMAT_MOVIES = "127.0.0.1:5000/waiter/dir/"
WAITER_IP_FORMAT_TVSHOWS = "127.0.0.1:5000/waiter/file/"


SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
os.environ["HTTPS"] = "off"
os.environ["wsgi.url_scheme"] = "http"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

MEDIA_URL = "/media/"
