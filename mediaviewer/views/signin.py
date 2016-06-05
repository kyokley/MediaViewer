from django.core.urlresolvers import reverse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render
from mediaviewer.views.home import (generateHeader,
                                    setSiteWideContext,
                                    )
from django.contrib.auth import authenticate, login
from mediaviewer.models.loginevent import LoginEvent
from datetime import datetime as dateObj
from django.utils.timezone import utc
from django.http import HttpResponseRedirect
from mysite.settings import DEBUG
from mediaviewer.utils import logAccessInfo

@logAccessInfo
def signin(request):
    context = {}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context['header'] = generateHeader('signin', request)
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
                raise Exception('Incorrect username or password!')
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

    if user:
        settings = user.settings()
        if not user.email or settings.force_password_change:
            return HttpResponseRedirect(reverse('mediaviewer:settings'))
        elif request.POST.has_key('next'):
            return HttpResponseRedirect(request.POST['next'])

    return render(request, 'mediaviewer/signin.html', context)
