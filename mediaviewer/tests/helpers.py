from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import UserSettings


def create_user(username='test_user',
                email='a@b.com',
                group_name='MediaViewer',
                send_email=False,
                force_password_change=False,
                is_staff=False):
    mv_group = Group.objects.filter(name=group_name).first()

    if not mv_group:
        mv_group = Group(name=group_name)
        mv_group.save()

    user = UserSettings.new(
            username,
            email,
            send_email=send_email,
            group=mv_group,
            is_staff=is_staff)
    settings = user.settings()
    settings.force_password_change = force_password_change
    return user
