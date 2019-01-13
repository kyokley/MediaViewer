# Django settings for site project.
import os
import logging
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."),
)

# Generate a secret key
# Borrowed from https://gist.github.com/ndarville/3452907
SECRET_FILE = os.path.join(BASE_DIR, 'secret.txt')
try:
    with open(SECRET_FILE, 'r') as secret_file:
        SECRET_KEY = secret_file.read().strip()
except IOError:
    try:
        import random
        SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz'
                                                           'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                                           '0123456789!@#$%^&*(-_=+)')
                                for i in range(50)])
        with open(SECRET_FILE, 'w') as secret_file:
            secret_file.write(SECRET_KEY)
    except IOError:
        Exception('Please create a %s file with random characters to generate your secret key!' % SECRET_FILE)

DEBUG = False
TEMPLATE_DEBUG = DEBUG
LOG_ACCESS_TIMINGS = False
IS_SYNCING = False

ADMINS = (
     ('AdminName', 'admin@email.com'),
)

MANAGERS = ADMINS

DATABASES = {
    # Testing settings!!!
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'dbname',                      # Or path to database file if using sqlite3.
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    },
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/static/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'djangobower.finders.BowerFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

MIDDLEWARE = (
    #'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mediaviewer.middleware.AutoLogout',
    #'axes.middleware.FailedLoginMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Auto logout delay in minutes
AUTO_LOGOUT_DELAY = 60

ROOT_URLCONF = 'mysite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'mysite.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'debug_toolbar',
    'widget_tweaks',
     #'django_memcached',
    'rest_framework',
    # 'djangobower',
    'mediaviewer',
    'mediaviewer.models',
    'mediaviewer.views',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
        '--with-coverage',
        '--cover-package=mediaviewer',
]

REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.BasicAuthentication',
            ),
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 30,
}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

AXES_CACHE = 'axes_cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'axes_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SYSTEM_BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(SYSTEM_BASE_PATH, 'logs')
LOG_FILE_NAME = os.path.join(LOG_DIR, 'mediaviewerLog')
loglevel = logging.DEBUG

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(SYSTEM_BASE_PATH, 'mediaviewer/templates/mediaviewer'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# BOWER_COMPONENTS_ROOT = os.path.join(PROJECT_ROOT, 'components')
# BOWER_INSTALLED_APPS = ('jquery',
                        # 'bootstrap',
                        # 'datatables.net',
                        # 'datatables.net-bs',
                        # 'datatables.net-responsive',
                        # 'datatables.net-responsive-bs',
                        # 'bootswatch-dist#slate',
                        # 'https://github.com/viralpatel/jquery.shorten.git',
                        # )

WAITER_HEAD = 'http://'
LOCAL_WAITER_IP_FORMAT_MOVIES = BANGUP_WAITER_IP_FORMAT_MOVIES = '127.0.0.1/waiter/dir/'
LOCAL_WAITER_IP_FORMAT_TVSHOWS = BANGUP_WAITER_IP_FORMAT_TVSHOWS = '127.0.0.1/waiter/file/'

WAITER_STATUS_URL = 'http://127.0.0.1/waiter/status'

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
os.environ['HTTPS'] = 'on'
os.environ['wsgi.url_scheme'] = 'https'

API_KEY = 'keykeykey'
OMDBAPI_KEY = None
IMAGE_PATH = 'mediaviewer/static/media/'

REQUEST_TIMEOUT = 3

# Run the python debugging smtp server with the following
# python -m smtpd -n -c DebuggingServer localhost:1025
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
EMAIL_FROM_ADDR = DEFAULT_FROM_EMAIL = 'testing@example.com'
BYPASS_SMTPD_CHECK = False

MINIMUM_PASSWORD_LENGTH = 6
TEMPORARY_PASSWORD = 'password' # Throwaway password set on user creation

MAXIMUM_NUMBER_OF_STORED_LOGIN_EVENTS = 10000
MAXIMUM_NUMBER_OF_STORED_DOWNLOAD_TOKENS = 10000

TOKEN_VALIDITY_LENGTH = 3 # In hours

# import django
# django.setup()
