from mysite.settings import *

DATABASES = {
    # Testing settings!!!
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'autodl',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}

BYPASS_SMTPD_CHECK = True
