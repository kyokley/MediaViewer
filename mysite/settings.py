# Django settings for site project.
import logging
import os

from pathlib import Path

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {message_constants.ERROR: "danger"}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."),
)

# Generate a secret key
# Borrowed from https://gist.github.com/ndarville/3452907
SECRET_FILE = os.path.join(BASE_DIR, "secret.txt")
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

DEBUG = False
TEMPLATE_DEBUG = DEBUG
LOG_ACCESS_TIMINGS = False
IS_SYNCING = False
USE_SILK = False

ADMINS = (("AdminName", "admin@email.com"),)

MANAGERS = ADMINS

DATABASES = {
    # Testing settings!!!
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "dbname",
        "USER": "db_user",
        "PASSWORD": "db_password",
        "HOST": "",
        "PORT": "",
    },
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

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

WEB_ROOT = Path(os.getenv("MV_WEB_ROOT")) if os.getenv("MV_WEB_ROOT") else Path("/var/www")
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = WEB_ROOT / "mv" / "media"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
# MEDIA_URL = '/static/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = WEB_ROOT / "mv" / "static"

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = "/static/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
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
    # 'django.middleware.security.SecurityMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "mediaviewer.middleware.AutoLogout",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_referrer_policy.middleware.ReferrerPolicyMiddleware",
    "mediaviewer.middleware.set_secure_headers",
)

# Auto logout delay in minutes
AUTO_LOGOUT_DELAY = 2880

ROOT_URLCONF = "mysite.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "mysite.wsgi.application"

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
            "level": "INFO",
            "propagate": False,
        },
    },
}

SYSTEM_BASE_PATH = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
LOG_DIR = Path(os.getenv("MV_LOG_DIR")) if os.getenv("MV_LOG_DIR") else SYSTEM_BASE_PATH / "logs"
LOG_FILE_NAME = LOG_DIR / "mediaviewerLog"
LOG_LEVEL = logging.DEBUG

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(SYSTEM_BASE_PATH, "mediaviewer/templates/mediaviewer"),
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

WAITER_HEAD = "http://"
WAITER_IP_FORMAT_MOVIES = "127.0.0.1/waiter/dir/"
WAITER_IP_FORMAT_TVSHOWS = "127.0.0.1/waiter/file/"

WAITER_STATUS_URL = "http://127.0.0.1/waiter/status"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
os.environ["HTTPS"] = "on"
os.environ["wsgi.url_scheme"] = "https"

# For SecurityMiddleware in django 3.0
# SECURE_REFERRER_POLICY = 'same-origin'
# SECURE_HSTS_SECONDS = 300
# SECURE_BROWSER_XSS_FILTER = True

# For pre-SecurityMiddleware in django 3.0
# Use django_referrer_policy middleware
REFERRER_POLICY = "same-origin"

API_KEY = os.environ.get("TVDB_API_KEY", "keykeykey")
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
BYPASS_SMTPD_CHECK = False

MINIMUM_PASSWORD_LENGTH = 6

MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS = 10000
MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS = 10000

TOKEN_VALIDITY_LENGTH = 3  # In hours
TOKEN_HOLDING_PERIOD = 168 # In hours
VIDEO_PROGRESS_HOLDING_PERIOD = 2160 # In hours

# PassKey Settings
PASSKEY_API_URL = os.environ.get("PASSKEY_API_URL")
PASSKEY_API_PRIVATE_KEY = os.environ.get("PASSKEY_API_PRIVATE_KEY")

# MediaWaiter Settings
WAITER_LOGIN = "waiter"
WAITER_PASSWORD_HASH = (
    os.environ.get("WAITER_PASSWORD_HASH")
    or "pbkdf2_sha256$260000$gTINkjUitLzAra3DGCJ4pK$/IzJql5fzVSV2XfINRkHpyBxIvNdjhxDyVqB3f5Lzmk="
)
