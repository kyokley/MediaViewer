from django.db import models
from django.contrib.auth.models import User
from mysite.settings import MINIMUM_PASSWORD_LENGTH
import re

LOCAL_IP = 'local_ip'
BANGUP_IP = 'bangup'
DEFAULT_SITE_THEME = 'default'
DARK_SITE_THEME = 'darkly'
UNITED_SITE_THEME = 'united'
JOURNAL_SITE_THEME = 'journal'
READABLE_SITE_THEME = 'readable'

TIMESTAMP_SORT = 'timestamp_sort'
FILENAME_SORT = 'filename_sort'

NUMBER_REGEX = re.compile(r'[0-9]')
CHAR_REGEX = re.compile(r'[a-zA-Z]')

class InvalidPasswordException(Exception):
    pass

class InvalidEmailException(Exception):
    pass

class UserSettings(models.Model):
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True)
    ip_format = models.TextField(db_column='ip_format', blank=False, null=False)
    user = models.ForeignKey('auth.User', null=False, db_column='userid', blank=False)
    can_download = models.BooleanField(db_column='can_download', blank=False, null=False)
    site_theme = models.TextField(db_column='site_theme')
    default_sort = models.TextField(db_column='default_sort')
    auto_download = models.BooleanField(db_column='auto_download', blank=False, null=False, default=False)
    force_password_change = models.BooleanField(db_column='force_password_change', blank=False, null=False, default=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'usersettings'

    def __unicode__(self):
        return 'id: %s u: %s ip: %s' % (self.id, self.user.username, self.ip_format)

    @classmethod
    def getSettings(cls, user):
        q = cls.objects.filter(user=user).only()
        return q and q[0] or None

setattr(User, 'settings', lambda x: UserSettings.getSettings(x))

def _has_number_validator(val):
    return bool(NUMBER_REGEX.search(val))

def _has_char_validator(val):
    return bool(CHAR_REGEX.search(val))

def _is_long_enough_validator(val):
    return len(val) >= MINIMUM_PASSWORD_LENGTH

def change_user_password(user,
                         old_password,
                         new_password,
                         confirm_new_password):
    if not user.check_password(old_password):
        raise InvalidPasswordException('Incorrect password')

    if new_password != confirm_new_password:
        raise InvalidPasswordException('New passwords do not match')

    if old_password == new_password:
        raise InvalidPasswordException('New and old passwords must be different')

    if not _has_number_validator(new_password):
        raise InvalidPasswordException('Password is too weak. Valid passwords must contain at least one numeric character.')

    if not _has_char_validator(new_password):
        raise InvalidPasswordException('Password is too weak. Valid passwords must contain at least one alphabetic character.')

    if not _is_long_enough_validator(new_password):
        raise InvalidPasswordException('Password is too weak. Valid passwords must be at least %s characters long.' % MINIMUM_PASSWORD_LENGTH)
    user.set_password(new_password)
    settings = user.settings()
    settings.force_password_change = False
    settings.save()
    user.save()

def _is_email_unique(user, val):
    return (user.email.lower() != val.lower() and
                not User.objects.filter(email__iexact=val).exists())

def set_email(user, email):
    if not _is_email_unique(user, email):
        raise InvalidEmailException('Email already exists on system. Please try another.')

    user.email = email
    user.save()
