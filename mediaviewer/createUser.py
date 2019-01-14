import sys
import os
from mediaviewer.models.usersettings import UserSettings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")


def createUser(name, email, can_download=True):
    '''
        Example usage of this script is as follows.
        ipython mediaviewer/createUser.py newUserName newUserEmail

        Be sure to set the PYTHONPATH env var to the folder
        containing the mediaviewer folder
    '''
    newUser = UserSettings.new(name,
                               email,
                               can_download=can_download,
                               )
    return newUser


if __name__ == '__main__':
    if len(sys.argv) == 3:
        createUser(sys.argv[1], sys.argv[2])
    else:
        print('Invalid number of arguments')
