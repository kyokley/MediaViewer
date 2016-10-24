from django.contrib.auth.decorators import login_required
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.usersettings import (UserSettings,
                                      LOCAL_IP,
                                      BANGUP_IP,
                                      FILENAME_SORT,
                                      )
from mediaviewer.views.home import generateHeader, setSiteWideContext
from django.shortcuts import render
from datetime import datetime as dateObj
from django.utils.timezone import utc
from mediaviewer.utils import logAccessInfo, check_force_password_change
from mediaviewer.log import log
from django.core.exceptions import ValidationError

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def settings(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
              'greeting': siteGreeting and siteGreeting.greeting or "Check out the new downloads!",
            }
    context['header'] = generateHeader('settings', request)
    user = request.user
    settings = user.settings()
    if settings:
        context['ip_format'] = settings.ip_format
    else:
        context['ip_format'] = BANGUP_IP
    context['title'] = 'Settings'
    context['auto_download'] = settings.auto_download

    context['email'] = user.email
    if not user.email:
        context['display_missing_email_modal'] = True
    else:
        context['display_missing_email_modal'] = False

    setSiteWideContext(context, request, includeMessages=False)

    return render(request, 'mediaviewer/settings.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def submitsettings(request):
    context = {'successful': True}
    context['header'] = generateHeader('submitsettings', request)
    setSiteWideContext(context, request)

    default_sort = request.POST.get('default_sort')
    if not default_sort:
        default_sort = FILENAME_SORT

    auto_download = request.POST.get('auto_download')
    if not auto_download:
        auto_download = False
    else:
        auto_download = auto_download == 'true'

    user = request.user
    settings = user.settings()
    if not settings:
        settings = UserSettings()
        settings.datecreated = dateObj.utcnow().replace(tzinfo=utc)
        settings.user = request.user
        changed = True
    else:
        changed = settings.default_sort != default_sort

    settings.auto_download = auto_download
    settings.default_sort = default_sort
    user.email = request.POST.get('email_field', user.email)
    context['default_sort'] = settings.default_sort

    if changed:
        settings.dateedited = dateObj.utcnow().replace(tzinfo=utc)

    settings.save()
    user.save()
    return render(request, 'mediaviewer/settingsresults.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def submitsitesettings(request):
    user = request.user
    context = {'successful': True}
    context['header'] = generateHeader('submitsitesettings', request)
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
        log.error("User is not a staffer!")
        context['errMsg'] = 'Unauthorized access attempted'
        context['successful'] = False
    return render(request, 'mediaviewer/settingsresults.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def submitnewuser(request):
    user = request.user
    context = {'successful': True}
    context['header'] = generateHeader('submitnewuser', request)
    setSiteWideContext(context, request)

    new_user_email = request.POST.get('new_user_email')
    if user.is_staff:
        if new_user_email:
            try:
                UserSettings.new(new_user_email,
                                 new_user_email,
                                 can_download=True,
                                 )
            except ValidationError, e:
                context['successful'] = False
                context['errMsg'] = e.message
            except Exception, e:
                context['successful'] = False
                context['errMsg'] = str(e)
    else:
        log.error("User is not a staffer!")
        context['errMsg'] = 'Unauthorized access attempted'
        context['successful'] = False
    return render(request, 'mediaviewer/settingsresults.html', context)
