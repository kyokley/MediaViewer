from django.contrib.auth.decorators import login_required
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.usersettings import (UserSettings,
                                      LOCAL_IP,
                                      BANGUP_IP,
                                      DEFAULT_SITE_THEME,
                                      FILENAME_SORT,
                                      )
from mediaviewer.views.home import generateHeader, setSiteWideContext
from django.shortcuts import render
from datetime import datetime as dateObj
from django.utils.timezone import utc
from mediaviewer.utils import logAccessInfo

@login_required(login_url='/mediaviewer/login/')
@logAccessInfo
def settings(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
              'greeting': siteGreeting and siteGreeting.greeting or "Check out the new downloads!",
            }
    headers = generateHeader('settings', request)
    context['header'] = headers[0]
    context['header2'] = headers[1]
    settings = request.user.settings()
    if settings:
        context['ip_format'] = settings.ip_format
    else:
        context['ip_format'] = LOCAL_IP
    context['title'] = 'Settings'
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, 'mediaviewer/settings.html', context)

@login_required(login_url='/mediaviewer/login/')
@logAccessInfo
def submitsettings(request):
    context = {}
    headers = generateHeader('submitsettings', request)
    context['header'] = headers[0]
    context['header2'] = headers[1]
    setSiteWideContext(context, request)

    default_sort = request.POST.get('default_sort')
    if not default_sort:
        default_sort = FILENAME_SORT

    site_theme = request.POST.get('site_theme')
    if not site_theme:
        site_theme = DEFAULT_SITE_THEME

    settings = request.user.settings()
    if not settings:
        settings = UserSettings()
        settings.datecreated = dateObj.utcnow().replace(tzinfo=utc)
        settings.user = request.user
        changed = True
    else:
        changed = (settings.default_sort != default_sort or
                   settings.site_theme != site_theme)

    settings.default_sort = default_sort
    settings.site_theme = site_theme
    context['site_theme'] = settings.site_theme
    context['default_sort'] = settings.default_sort

    if changed:
        settings.dateedited = dateObj.utcnow().replace(tzinfo=utc)

    settings.save()
    return render(request, 'mediaviewer/settingsresults.html', context)

@login_required(login_url='/mediaviewer/login/')
@logAccessInfo
def submitsitesettings(request):
    user = request.user
    context = {}
    headers = generateHeader('submitsitesettings', request)
    context['header'] = headers[0]
    context['header2'] = headers[1]
    setSiteWideContext(context, request)

    newGreeting = request.POST.get('greeting')
    latestGreeting = SiteGreeting.latestSiteGreeting()

    if user.is_staff:
        if not latestGreeting or newGreeting != latestGreeting.greeting:
            newSiteGreeting = SiteGreeting()
            newSiteGreeting.greeting = newGreeting
            newSiteGreeting.datecreated = dateObj.utcnow().replace(tzinfo=utc)
            newSiteGreeting.user = request.user
            newSiteGreeting.save()
    else:
        raise Exception("User is not a staffer!")
    return render(request, 'mediaviewer/settingsresults.html', context)

