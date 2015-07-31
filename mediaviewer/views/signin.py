from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render
from mediaviewer.views.home import (generateHeader,
                                    setSiteWideContext,
                                    )
from django.contrib.auth import authenticate, login
from mediaviewer.models.loginevent import LoginEvent
from datetime import datetime as dateObj
from django.utils.timezone import utc
from ipware.ip import get_ip
from django.http import HttpResponseRedirect
from mediaviewer.models.usersettings import (
                                      LOCAL_IP,
                                      BANGUP_IP,
                                      )
from mysite.settings import DEBUG
from mediaviewer.utils import logAccessInfo

import socket

from mediaviewer.log import log

@logAccessInfo
def signin(request):
    context = {}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    headers = generateHeader('signin', request)
    context['header'] = headers[0]
    context['header2'] = headers[1]
    context['greeting'] = siteGreeting and siteGreeting.greeting or "SignIn"
    setSiteWideContext(context, request)
    user = None

    if request.GET.has_key('next'):
        context['next'] = request.GET['next']

    try:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is None:
                raise Exception('Invalid User')
            else:
                if user.is_active:
                    login(request, user)
                    context['loggedin'] = True
                    context['user'] = request.user
                    le = LoginEvent()
                    le.user = request.user
                    le.datecreated = dateObj.utcnow().replace(tzinfo=utc)
                    le.save()
    except Exception, e:
        if DEBUG:
            context['error_message'] = str(e)
        else:
            context['error_message'] = 'Incorrect username or password!'

    if user and request.POST.has_key('next'):
        return HttpResponseRedirect(request.POST['next'])

    return render(request, 'mediaviewer/signin.html', context)

