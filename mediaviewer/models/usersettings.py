from django.db import models
from django.contrib.auth.models import (User,
                                        Group,
                                        )
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.utils import IntegrityError
from mysite.settings import (TEMPORARY_PASSWORD,
                             TIME_ZONE,
                             )
from mediaviewer.forms import FormlessPasswordReset
from datetime import datetime
import pytz
import re

LOCAL_IP = 'local_ip'
BANGUP_IP = 'bangup'

TIMESTAMP_SORT = 'timestamp_sort'
FILENAME_SORT = 'filename_sort'

class ImproperLogin(Exception):
    pass
class BadEmail(Exception):
    pass

EMAIL_REGEX = re.compile('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

class UserSettings(models.Model):
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True)
    ip_format = models.TextField(db_column='ip_format', blank=False, null=False)
    user = models.ForeignKey('auth.User', null=False, db_column='userid', blank=False)
    can_download = models.BooleanField(db_column='can_download', blank=False, null=False)
    default_sort = models.TextField(db_column='default_sort')
    auto_download = models.BooleanField(db_column='auto_download', blank=False, null=False, default=False)
    force_password_change = models.BooleanField(db_column='force_password_change', blank=False, null=False, default=False)
    can_login = models.BooleanField(db_column='can_login', blank=False, null=False, default=True)
    binge_mode = models.BooleanField(blank=False, null=False, default=True)
    last_watched = models.ForeignKey('mediaviewer.Path', null=True, blank=True)
    jump_to_last_watched = models.BooleanField(blank=False, null=False, default=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'usersettings'

    def __unicode__(self):
        return 'id: %s u: %s ip: %s' % (self.id, self.user.username, self.ip_format)

    @classmethod
    def getSettings(cls, user):
        q = cls.objects.filter(user=user).only()
        return q and q[0] or None

    @classmethod
    @transaction.atomic
    def new(cls,
            name,
            email,
            is_staff=False,
            is_superuser=False,
            ip_format=BANGUP_IP,
            default_sort=FILENAME_SORT,
            can_download=True,
            send_email=True,
            binge_mode=True,
            jump_to_last_watched=True,
            ):
        ''' Create new User and associated UserSettings '''

        validate_email(email)

        if User.objects.filter(username__iexact=name).exists():
            raise IntegrityError('Username already exists')
        elif User.objects.filter(email__iexact=email).exists():
            raise IntegrityError('Email already exists')

        newUser = User()
        newUser.username = name
        newUser.is_staff = is_staff
        newUser.is_superuser = is_superuser
        newUser.set_password(TEMPORARY_PASSWORD)
        newUser.save()

        mv_group = Group.objects.get(name='MediaViewer')
        mv_group.user_set.add(newUser)
        mv_group.save()

        newSettings = cls()
        newSettings.datecreated = datetime.now(pytz.timezone(TIME_ZONE))
        newSettings.dateedited = newSettings.datecreated
        newSettings.user = newUser
        newSettings.ip_format = ip_format
        newSettings.default_sort = default_sort
        newSettings.can_download = can_download
        newSettings.can_login = False
        newSettings.binge_mode = binge_mode
        newSettings.jump_to_last_watched = jump_to_last_watched
        newSettings.save()

        if send_email:
            fake_form = FormlessPasswordReset(newUser, email)
            fake_form.save(email_template_name='mediaviewer/password_create_email.html',
                           subject_template_name='mediaviewer/password_create_subject.txt',
                           )

        return newUser

setattr(User, 'settings', lambda x: UserSettings.getSettings(x))

def case_insensitive_authenticate(username, password):
    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return None

    return authenticate(username=user.username, password=password)

def validate_email(email):
    if not EMAIL_REGEX.search(email):
        raise BadEmail('Email address is not valid')
