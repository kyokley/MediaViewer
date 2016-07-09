from django.core.urlresolvers import reverse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render
from mediaviewer.views.home import (generateHeader,
                                    setSiteWideContext,
                                    )
from django.contrib.auth import login
from mediaviewer.models.loginevent import LoginEvent
from datetime import datetime as dateObj
from django.utils.timezone import utc
from django.http import HttpResponseRedirect
from mysite.settings import DEBUG
from mediaviewer.utils import logAccessInfo
from mediaviewer.models.usersettings import (ImproperLogin,
                                             case_insensitive_authenticate,
                                             )

@logAccessInfo
def signin(request):
    context = {'loggedin': False}
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
            user = case_insensitive_authenticate(username=username, password=password)
            if user is None:
                raise Exception('Incorrect username or password!')
            elif not user.settings().can_login:
                raise ImproperLogin('You should have received an email with a link to set up your password the first time. '
                                    'Please follow the instructions in the email.')
            else:
                if user.is_active:
                    login(request, user)
                    context['loggedin'] = True
                    context['user'] = request.user
                    LoginEvent.new(request.user,
                                   dateObj.utcnow().replace(tzinfo=utc),
                                   )

        if user:
            settings = user.settings()
            if not user.email or settings.force_password_change:
                return HttpResponseRedirect(reverse('mediaviewer:settings'))
            elif request.POST.has_key('next'):
                return HttpResponseRedirect(request.POST['next'])
    except ImproperLogin, e:
        context['error_message'] = str(e)
    except Exception, e:
        if DEBUG:
            context['error_message'] = str(e)
        else:
            context['error_message'] = 'Incorrect username or password!'

    return render(request, 'mediaviewer/signin.html', context)
