from django.db import models
from django.contrib.auth.models import User

LOCAL_IP = 'local_ip'
BANGUP_IP = 'bangup'
DEFAULT_SITE_THEME = 'default'
DARK_SITE_THEME = 'darkly'
UNITED_SITE_THEME = 'united'
JOURNAL_SITE_THEME = 'journal'
READABLE_SITE_THEME = 'readable'

TIMESTAMP_SORT = 'timestamp_sort'
FILENAME_SORT = 'filename_sort'

class UserSettings(models.Model):
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True)
    ip_format = models.TextField(db_column='ip_format', blank=False, null=False)
    user = models.ForeignKey('auth.User', null=False, db_column='userid', blank=False)
    can_download = models.BooleanField(db_column='can_download', blank=False, null=False)
    site_theme = models.TextField(db_column='site_theme')
    default_sort = models.TextField(db_column='default_sort')
    auto_download = models.BooleanField(db_column='auto_download', blank=False, null=False, default=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'usersettings'

    def __unicode__(self):
        return 'id: %s u: %s ip: %s' % (self.id, self.user.username, self.ip_format)

    @classmethod
    def getSettings(cls, user):
        q = cls.objects.filter(user=user).only()
        return q and q[0] or None

    @staticmethod
    def change_password(user,
                        old_password,
                        new_password,
                        confirm_new_password):
        if (user.check_password(old_password) and
                new_password == confirm_new_password):
            user.set_password(new_password)
            return True
        return False

setattr(User, 'settings', lambda x: UserSettings.getSettings(x))
