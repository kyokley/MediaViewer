from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import UserSettings


def create_user(username='test_user',
                email='a@b.com',
                group_name='MediaViewer',
                send_email=False,
                force_password_change=False):
        if not Group.objects.filter(name=group_name).exists():
            mv_group = Group(name=group_name)
            mv_group.save()

        user = UserSettings.new(
                username,
                email,
                send_email=send_email,
                group=mv_group)
        settings = user.settings()
        settings.force_password_change = force_password_change
        return user
