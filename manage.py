#!/usr/bin/env python
import os
import sys
from mediaviewer.utils import checkSMTPServer

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

    from django.core.management import execute_from_command_line

    if 'runserver' in sys.argv:
        checkSMTPServer()
    execute_from_command_line(sys.argv)
