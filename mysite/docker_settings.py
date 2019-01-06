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
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'postgres',                      # Or path to database file if using sqlite3.
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'postgres',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    },
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mediaviewer.middleware.AutoLogout',
    #'axes.middleware.FailedLoginMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

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
    'widget_tweaks',
    #'django_memcached',
    'rest_framework',
    'djangobower',
    'mediaviewer',
    'mediaviewer.models',
    'mediaviewer.views',
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
