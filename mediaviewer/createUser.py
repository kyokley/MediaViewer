import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

from django.db import transaction
from datetime import datetime as dateObj
from django.utils.timezone import utc
from django.contrib.auth.models import User
from mediaviewer.models.usersettings import (UserSettings,
                                             BANGUP_IP,
                                             DEFAULT_SITE_THEME,
                                             FILENAME_SORT,
                                             )

''' 
    Example usage of this script is as follows.
    ipython mediaviewer/createUser.py newUserName

    Be sure to set the PYTHONPATH env var to the folder
    containing the mediaviewer folder
'''

@transaction.atomic
def createUser(name, can_download=True):
    newUser = User()
    newUser.username = name
    newUser.is_staff = False
    newUser.is_superuser = False
    newUser.save()

    newSettings = UserSettings()
    newSettings.datecreated = dateObj.utcnow().replace(tzinfo=utc)
    newSettings.dateedited = newSettings.datecreated
    newSettings.user = newUser
    newSettings.ip_format = BANGUP_IP
    newSettings.default_sort = FILENAME_SORT
    newSettings.site_theme = DEFAULT_SITE_THEME
    newSettings.can_download = can_download
    newSettings.save()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        createUser(sys.argv[1])
