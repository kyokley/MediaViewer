from django.urls import reverse
from django.contrib.auth.views import (
    PasswordChangeView,
)
from mediaviewer.forms import (
    MVPasswordChangeForm,
)


def change_password():
    return PasswordChangeView.as_view(
        template_name="mediaviewer/change_password.html",
        success_url=reverse("mediaviewer:change_password_submit"),
        form_class=MVPasswordChangeForm,
    )
