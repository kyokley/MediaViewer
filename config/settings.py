# Django settings for site project.
import os
from pathlib import Path

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {message_constants.ERROR: "danger"}

BASE_DIR = Path(__file__).parent.parent

# Generate a secret key
# Borrowed from https://gist.github.com/ndarville/3452907
SECRET_FILE = os.environ.get("MV_SECRET_FILE", BASE_DIR / "secret.txt")
try:
    with open(SECRET_FILE, "r") as secret_file:
        SECRET_KEY = secret_file.read().strip()
except IOError:
    try:
        import random

        SECRET_KEY = "".join(
            [
                random.SystemRandom().choice(
                    "abcdefghijklmnopqrstuvwxyz"
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789!@#$%^&*(-_=+)"
                )
                for i in range(50)
            ]
        )
        with open(SECRET_FILE, "w") as secret_file:
            secret_file.write(SECRET_KEY)
    except IOError:
        Exception(
            f"Please create a {SECRET_FILE} file with random characters "
            f"to generate your secret key!"
        )

LOG_ACCESS_TIMINGS = False
IS_SYNCING = False

ADMINS = (("AdminName", "admin@email.com"),)
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

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "America/Chicago"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Example: "/var/www/example.com/media/"
MEDIA_ROOT = (
    Path(os.environ["MV_MEDIA_ROOT"])
    if os.environ.get("MV_MEDIA_ROOT")
    else Path(__file__).parent.parent / "media"
)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = "/media/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = (
    Path(os.environ["MV_STATIC_DIR"])
    if os.environ.get("MV_STATIC_DIR")
    else Path(__file__).parent.parent / "static"
)

NPM_STATIC_ROOT = (
    Path(os.environ["MV_NPM_STATIC_DIR"])
    if os.environ.get("MV_NPM_STATIC_DIR")
    else Path(__file__).parent.parent / "node_modules"
)

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = "/static/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    NPM_STATIC_ROOT,
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "mediaviewer.middleware.AutoLogout",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "mediaviewer.middleware.set_secure_headers",
)

# Auto logout delay in minutes
AUTO_LOGOUT_DELAY = 2880

ROOT_URLCONF = "config.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "config.wsgi.application"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "grappelli",  # Required to come before django.contrib.admin
    # Uncomment the next line to enable the admin:
    "django.contrib.admin",
    # Uncomment the next line to enable admin documentation:
    "django.contrib.admindocs",
    "widget_tweaks",
    "rest_framework",
    "mediaviewer",
)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "mediaviewer.authenticators.WaiterSettingsAuthBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAdminUser",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": ("rest_framework.pagination.PageNumberPagination"),
    "PAGE_SIZE": 100,
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.core": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

SYSTEM_BASE_PATH = Path(__file__).parent.parent

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            SYSTEM_BASE_PATH / "mediaviewer/templates/mediaviewer",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

GRAPPELLI_ADMIN_TITLE = "MediaViewer Admin"

# WAITER_DOMAIN should be like "http://127.0.0.1:5000"
_waiter_domain = os.environ["MV_WAITER_DOMAIN"]
WAITER_DOMAIN = (
    _waiter_domain if not _waiter_domain.endswith("/") else _waiter_domain[:-1]
)
WAITER_STATUS_URL = f"{WAITER_DOMAIN}/waiter/status"
WAITER_IP_FORMAT_MOVIES = f"{WAITER_DOMAIN}/waiter/dir/"
WAITER_IP_FORMAT_TVSHOWS = f"{WAITER_DOMAIN}/waiter/file/"

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# os.environ["HTTPS"] = "on"
# os.environ["wsgi.url_scheme"] = "https"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
os.environ["HTTPS"] = "off"
os.environ["wsgi.url_scheme"] = "http"

# For SecurityMiddleware in django 3.0
SECURE_REFERRER_POLICY = "same-origin"
SECURE_HSTS_SECONDS = 300
SECURE_BROWSER_XSS_FILTER = True

API_KEY = os.environ.get("MV_TVDB_API_KEY", "keykeykey")
IMAGE_PATH = "mediaviewer/static/media/"

REQUEST_TIMEOUT = 20

# Run the python debugging smtp server with the following
# python -m smtpd -n -c DebuggingServer localhost:1025
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""  # nosec
EMAIL_USE_TLS = False
EMAIL_FROM_ADDR = DEFAULT_FROM_EMAIL = "testing@example.com"

MINIMUM_PASSWORD_LENGTH = 6

MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS = 10000
MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS = 10000

TOKEN_VALIDITY_LENGTH = 3  # In hours
TOKEN_HOLDING_PERIOD = 168  # In hours
VIDEO_PROGRESS_HOLDING_PERIOD = 2160  # In hours

# PassKey Settings
PASSKEY_API_URL = os.environ.get("MV_PASSKEY_API_URL")
PASSKEY_API_PRIVATE_KEY = os.environ.get("MV_PASSKEY_API_PRIVATE_KEY")

# MediaWaiter Settings
WAITER_LOGIN = "waiter"
WAITER_PASSWORD_HASH = (
    os.environ.get("MV_WAITER_PASSWORD_HASH")
    or "pbkdf2_sha256$260000$gTINkjUitLzAra3DGCJ4pK$/IzJql5fzVSV2XfINRkHpyBxIvNdjhxDyVqB3f5Lzmk="
)

SKIP_LOADING_TVDB_CONFIG = int(os.environ.get("MV_SKIP_LOADING_TVDB_CONFIG", 0)) == 1

USE_SILK = DEBUG = os.environ.get("MV_DEBUG", "false").lower() == "true"

TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = os.environ.get("MV_ALLOWED_HOSTS", "").split(",") or [
    "localhost",
    "127.0.0.1",
    "mediaviewer",
]

if DEBUG:
    INSTALLED_APPS += (
        "silk",
        "debug_toolbar",
    )

    MIDDLEWARE = ("silk.middleware.SilkyMiddleware",) + MIDDLEWARE

    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
