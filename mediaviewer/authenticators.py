from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User


class SettingsBackend(BaseBackend):
    def _validate(self, username, password):
        raise NotImplementedError("Function must be implemented by child classes")

    def authenticate(self, request, username=None, password=None):
        valid = self._validate(username, password)

        if valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. There's no need to set a password
                # because only the password from settings.py is checked.
                user = User(username=username)
                user.is_staff = True
                user.is_superuser = False
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class WaiterSettingsAuthBackend(SettingsBackend):
    """
    Authenticate against the settings WAITER_LOGIN and WAITER_PASSWORD_HASH.

    Use the login name and a hash of the password. For example:

    WAITER_LOGIN = 'auth0'
    WAITER_PASSWORD = (
        'pbkdf2_sha256$30000$Vo0VlMnkR4Bk$qEvtdyZRWTcOsCnI/oQ7fVOu1XAURIZYoOZ3iq8Dr4M='
        )

    To get the hashed pass do the following in `python manage.py shell_plus`:
    >>> from django.contrib.auth.hashers import PBKDF2PasswordHasher
    >>> hasher = PBKDF2PasswordHasher()
    >>> hasher.encode(<password>, hasher.salt())
    'pbkdf2_sha256$260000$k5HZABEEptjiaWOdbTsZDy$BWkdWxyYO2XcQZIICi/5RKbICQvJEcwFZZbFpNENYiw='
    """
    def _validate(self, username, password):
        login_valid = settings.WAITER_LOGIN == username
        pwd_valid = check_password(password, settings.WAITER_PASSWORD_HASH)
        return login_valid and pwd_valid
