import re
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, User
from django.db import models, transaction
from django.db.utils import IntegrityError

from mediaviewer.forms import FormlessPasswordReset


TIMESTAMP_SORT = "timestamp_sort"
FILENAME_SORT = "filename_sort"


class ImproperLogin(Exception):
    pass


class BadEmail(Exception):
    pass


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


class UserSettings(models.Model):
    DARK = "dark"
    LIGHT = "light"

    THEME_CHOICES = (
        (DARK, "Dark"),
        (LIGHT, "Light"),
    )

    datecreated = models.DateTimeField(db_column="datecreated", blank=True)
    dateedited = models.DateTimeField(db_column="dateedited", blank=True)
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        db_column="userid",
        blank=False,
    )
    can_download = models.BooleanField(
        db_column="can_download", blank=False, null=False
    )
    default_sort = models.TextField(db_column="default_sort")
    force_password_change = models.BooleanField(
        db_column="force_password_change", blank=False, null=False, default=False
    )
    can_login = models.BooleanField(
        db_column="can_login", blank=False, null=False, default=True
    )
    binge_mode = models.BooleanField(blank=False, null=False, default=True)
    last_watched_tv = models.ForeignKey(
        "mediaviewer.TV", on_delete=models.SET_NULL, null=True, blank=True
    )
    last_watched_movie = models.ForeignKey(
        "mediaviewer.Movie", on_delete=models.SET_NULL, null=True, blank=True
    )
    jump_to_last_watched = models.BooleanField(blank=False, null=False, default=True)
    allow_password_logins = models.BooleanField(blank=True, null=False, default=False)

    theme = models.CharField(
        max_length=32, blank=False, null=False, default=DARK, choices=THEME_CHOICES
    )

    class Meta:
        app_label = "mediaviewer"
        db_table = "usersettings"
        verbose_name_plural = "User Settings"

    def __str__(self):
        return f"id: {self.id} u: {self.user.username}"

    @property
    def username(self):
        return self.user.username

    @classmethod
    def getSettings(cls, user):
        q = cls.objects.filter(user=user).only()
        return q and q[0] or None

    @classmethod
    def create_user_setting(
        cls,
        user,
        default_sort=FILENAME_SORT,
        can_login=False,
        can_download=True,
        binge_mode=True,
        jump_to_last_watched=True,
    ):
        newSettings = cls()
        newSettings.datecreated = datetime.now(pytz.timezone(settings.TIME_ZONE))
        newSettings.dateedited = newSettings.datecreated
        newSettings.user = user
        newSettings.default_sort = default_sort
        newSettings.can_download = can_download
        newSettings.can_login = can_login
        newSettings.binge_mode = binge_mode
        newSettings.jump_to_last_watched = jump_to_last_watched
        newSettings.save()
        return newSettings

    @classmethod
    @transaction.atomic
    def new(
        cls,
        name,
        email,
        is_staff=False,
        is_superuser=False,
        default_sort=FILENAME_SORT,
        can_download=True,
        send_email=True,
        binge_mode=True,
        jump_to_last_watched=True,
        group=None,
    ):
        """Create new User and associated UserSettings"""

        validate_email(email)

        if name is None:
            name = email

        if User.objects.filter(username__iexact=name).exists():
            raise IntegrityError("Username already exists")
        elif User.objects.filter(email__iexact=email).exists():
            raise IntegrityError("Email already exists")

        newUser = User()
        newUser.username = name.lower().strip()
        newUser.email = email.lower().strip()
        newUser.is_staff = is_staff
        newUser.is_superuser = is_superuser
        # Password reset emails are only sent for user that have passwords
        # Create a random password for the time being
        newUser.set_password(User.objects.make_random_password())
        newUser.save()

        cls.create_user_setting(
            newUser,
            default_sort=default_sort,
            can_login=True,
            can_download=can_download,
            binge_mode=binge_mode,
            jump_to_last_watched=jump_to_last_watched,
        )

        if group:
            mv_group = group
        else:
            mv_group = Group.objects.get(name="MediaViewer")
        mv_group.user_set.add(newUser)
        mv_group.save()

        if send_email:
            fake_form = FormlessPasswordReset(newUser, email)
            fake_form.save(
                email_template_name="mediaviewer/password_create_email.html",
                subject_template_name="mediaviewer/password_create_subject.txt",  # noqa
            )

        return newUser


setattr(User, "settings", lambda x: UserSettings.getSettings(x))


def case_insensitive_authenticate(request, username, password):
    """Attempt password-based user login"""
    try:
        user = User.objects.get(username__iexact=username)
        settings = user.settings()
        if not settings.allow_password_logins:
            return None
    except User.DoesNotExist:
        return None

    return authenticate(request=request, username=user.username, password=password)


def validate_email(email):
    if not EMAIL_REGEX.search(email):
        raise BadEmail("Email address is not valid")
