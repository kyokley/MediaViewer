from mysite.settings import *

import os

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

ADMINS = (
    ('Docker', 'docker@example.com'),
)
MANAGERS = ADMINS

DATABASES = {
    # Testing settings!!!
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'postgres',
        'PORT': '',  # Set to empty string for default.
    },
}

INSTALLED_APPS += (
    'django_nose',
)

MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

WAITER_STATUS_URL = 'http://127.0.0.1:5000/waiter/status'
WAITER_HEAD = 'http://'
BANGUP_WAITER_IP_FORMAT_MOVIES = '127.0.0.1:5000/waiter/dir/'
BANGUP_WAITER_IP_FORMAT_TVSHOWS = '127.0.0.1:5000/waiter/file/'

BYPASS_SMTPD_CHECK = True

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
os.environ['HTTPS'] = 'off'
os.environ['wsgi.url_scheme'] = 'http'

STATIC_FILES_DIRS = (
    '/home/docker/code/static',
)
