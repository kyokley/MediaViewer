from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.utils import getSomewhatUniqueID

DEFAULT_USERNAME = "test_user"
DEFAULT_EMAIL = "a@b.com"


def create_user(
    username=DEFAULT_USERNAME,
    email=DEFAULT_EMAIL,
    group_name="MediaViewer",
    send_email=False,
    force_password_change=False,
    is_staff=False,
    random=False,
):
    mv_group = Group.objects.filter(name=group_name).first()

    if not mv_group:
        mv_group = Group(name=group_name)
        mv_group.save()

    if random:
        if username != DEFAULT_USERNAME or email != DEFAULT_EMAIL:
            raise ValueError(
                "Username and email are not expected to be populated"
                " when used with random kwarg"
            )

        username = getSomewhatUniqueID()
        email = "{}@{}.com".format(
            str(getSomewhatUniqueID()), str(getSomewhatUniqueID())
        )

    user = UserSettings.new(
        username, email, send_email=send_email, group=mv_group, is_staff=is_staff
    )
    settings = user.settings()
    settings.force_password_change = force_password_change
    return user
