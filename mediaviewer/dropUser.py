import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

from django.contrib.auth.models import User


def dropUser(username):
    '''
        Example usage of this script is as follows.
        ipython mediaviewer/dropUser.py username

        Be sure to set the PYTHONPATH env var to the folder
        containing the mediaviewer folder
    '''
    user = User.objects.get(username=username)
    if user:
        user.delete()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        dropUser(sys.argv[1])
    else:
        print('Invalid number of arguments')

