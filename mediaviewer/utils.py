# Based on an example from http://masnun.com/2010/01/01/sending-mail-via-postfix-a-perfect-python-example.html
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from datetime import datetime
from binascii import hexlify
from functools import wraps
from django.http import HttpResponse

from mysite.settings import (LOG_ACCESS_TIMINGS,
                             EMAIL_FROM_ADDR,
                             EMAIL_HOST,
                             EMAIL_PORT,
                             BYPASS_SMTPD_CHECK,
                             )

import os
import json
import telnetlib

from mediaviewer.log import log

def getSomewhatUniqueID(numBytes=4):
    return hexlify(os.urandom(numBytes))

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
        except Exception, e:
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

def json_response(func):
    """
    A decorator thats takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)
        if isinstance(objects, HttpResponse):
            return objects
        try:
            data = json.dumps(objects)
            if 'callback' in request.REQUEST:
                # a jsonp response!
                data = '%s(%s);' % (request.REQUEST['callback'], data)
                return HttpResponse(data, "text/javascript")
        except:
            data = json.dumps(str(objects))
        return HttpResponse(data, "application/json")
    return decorator

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def sendMail(to_addr, subject, text, from_addr=EMAIL_FROM_ADDR, files=None, server='localhost'):
    if type(to_addr) is not list:
        to_addr = [to_addr]
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

    smtp = smtplib.SMTP(server)
    smtp.sendmail(from_addr, to_addr, msg.as_string())
    smtp.close()

def checkSMTPServer():
    if not BYPASS_SMTPD_CHECK:
        smtp_server = telnetlib.Telnet(host=EMAIL_HOST,
                                       port=EMAIL_PORT)
        smtp_server.close()

def check_force_password_change(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        from mediaviewer.views.password_reset import change_password
        request = args and args[0]
        if request and request.user:
            user = request.user
            if user.is_authenticated():
                settings = user.settings()
                if settings.force_password_change:
                    return change_password(request)
        res = func(*args, **kwargs)
        return res
    return wrap
