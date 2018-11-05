from django.contrib.auth.models import Group
from mediaviewer.models.usersettings import UserSettings


def create_user(group_name='MediaViewer',
                username='test_user',
                email='a@b.com',
                send_email=False):
        mv_group = Group(name=group_name)
        mv_group.save()

        user = UserSettings.new(
                username,
                email,
                send_email=send_email)
        settings = user.settings()
        settings.force_password_change = False
        return user
