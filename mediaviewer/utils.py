# Based on an example from http://masnun.com/2010/01/01/sending-mail-via-postfix-a-perfect-python-example.html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders as Encoders
from datetime import datetime
from binascii import hexlify
from functools import wraps

from mysite.settings import (LOG_ACCESS_TIMINGS,
                             EMAIL_FROM_ADDR,
                             EMAIL_HOST,
                             EMAIL_PORT,
                             BYPASS_SMTPD_CHECK,
                             )
from django.contrib.auth.models import User

import os
import telnetlib  # nosec

from mediaviewer.log import log

SUFFIXES = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
COMMASPACE = ', '


def getSomewhatUniqueID(numBytes=4):
    return hexlify(os.urandom(numBytes)).decode('ascii')


def logAccessInfo(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        id = getSomewhatUniqueID()
        request = args and args[0]
        username = None
        if LOG_ACCESS_TIMINGS:
            start = datetime.now()

        if not request:
            log.debug('%s: No request' % id)
        elif request.user and request.user.username:
            username = request.user.username
            log.debug('%s: %s is accessing %s' % (id, username, func.__name__))
        else:
            log.debug('%s: Got request but no user' % id)

        if kwargs:
            log.debug('%s: With kwargs:\n%s' % (id, kwargs))

        try:
            res = func(*args, **kwargs)
        except Exception as e:
            # Log unhandled exceptions
            log.error('%s: %s' % (id, e), exc_info=True)
            log.error('%s: Access attempted with following vars...' % id)
            log.error('%s: %s' % (id, locals()))
            raise

        if LOG_ACCESS_TIMINGS:
            finished = datetime.now()
            log.debug('%s: page started at: %s' % (id, start))
            log.debug('%s: page finished at: %s' % (id, finished))
            log.debug('%s: page total took: %s' % (id, finished - start))

        return res
    return wrap


def humansize(nbytes):
    if nbytes == 0:
        return '0 B'

    i = 0
    while nbytes >= 1024 and i < len(SUFFIXES)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, SUFFIXES[i])


def sendMail(
        to_addr,
        subject,
        text,
        from_addr=EMAIL_FROM_ADDR,
        files=None,
        server='localhost'):
    if not isinstance(to_addr, list):
        to_addr = set([to_addr])
    else:
        to_addr = set(to_addr)

    if not files:
        files = []
    if type(files) is not list:
        files = [files]

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = COMMASPACE.join(to_addr)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text, 'html'))

    for file in files:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(file, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="%s"' % os.path.basename(file))
        msg.attach(part)

    # BCC staff members by adding them to recipient list
    staff = User.objects.filter(is_staff=True)
    for user in staff:
        if user.email:
            to_addr.add(user.email)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(from_addr, to_addr, msg.as_string())
    smtp.close()


def checkSMTPServer():
    if not BYPASS_SMTPD_CHECK:
        smtp_server = telnetlib.Telnet(host=EMAIL_HOST,  # nosec
                                       port=EMAIL_PORT)
        smtp_server.close()
