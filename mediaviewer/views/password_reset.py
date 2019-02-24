from functools import wraps

from django.urls import reverse
from django.contrib.auth.views import (
                                       PasswordChangeView,
                                       )
from mediaviewer.forms import (
                               MVPasswordChangeForm,
                               )


def change_password():
    return PasswordChangeView.as_view(
            template_name='mediaviewer/change_password.html',
            success_url=reverse('mediaviewer:change_password_submit'),
            form_class=MVPasswordChangeForm,
            )


def check_force_password_change(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        request = args and args[0]
        if request and request.user:
            user = request.user
            if user.is_authenticated:
                settings = user.settings()
                if settings.force_password_change:
                    return change_password()
        res = func(*args, **kwargs)
        return res
    return wrap
