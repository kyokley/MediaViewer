from django.core.urlresolvers import reverse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth import login
from mediaviewer.models.loginevent import LoginEvent
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
    context['active_page'] = 'signin'
    context['greeting'] = siteGreeting and siteGreeting.greeting or "SignIn"
    user = request.user

    if 'next' in request.GET:
        context['next'] = request.GET['next']

    if not user.is_authenticated:
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
                        LoginEvent.new(request.user)
                    else:
                        raise ImproperLogin('User is no longer active')

        except ImproperLogin as e:
            context['error_message'] = str(e)
        except Exception as e:
            if DEBUG:
                context['error_message'] = str(e)
            else:
                context['error_message'] = 'Incorrect username or password!'

    if (user and
            user.is_authenticated and
            not context.get('error_message')):
        settings = user.settings()
        setSiteWideContext(context, request)
        if not user.email or settings.force_password_change:
            return HttpResponseRedirect(reverse('mediaviewer:settings'))
        elif 'next' in request.POST and request.POST['next']:
            return HttpResponseRedirect(request.POST['next'])
        else:
            if request.method == 'GET':
                return render(request, 'mediaviewer/signin.html', context)
            else:
                return HttpResponseRedirect(reverse('mediaviewer:signin'))

    return render(request, 'mediaviewer/signin.html', context)
