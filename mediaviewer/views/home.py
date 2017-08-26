from django.http import HttpResponse
from mediaviewer.models.usersettings import (
                                      FILENAME_SORT,
                                      )
from mediaviewer.models.message import (Message,
                                        REGULAR,
                                        LAST_WATCHED,
                                        )
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.waiterstatus import WaiterStatus
from django.shortcuts import render
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.utils import logAccessInfo, check_force_password_change
from mysite.settings import DEBUG

import json

from mediaviewer.log import log

def setSiteWideContext(context, request, includeMessages=False):
    user = request.user
    if user.is_authenticated():
        settings = user.settings()
        context['loggedin'] = True
        context['user'] = user
        context['default_sort'] = settings and settings.default_sort or FILENAME_SORT
        if includeMessages:
            for message in Message.getMessagesForUser(request.user, message_type=REGULAR):
                Message.add_message(request,
                        message.level,
                        message.body,
                        extra_tags=str(message.id))

            for message in Message.getMessagesForUser(request.user, message_type=LAST_WATCHED):
                Message.add_message(request,
                        message.level,
                        message.body,
                        extra_tags=str(message.id))

        context['movie_genres'] = File.get_movie_genres()
        context['tv_genres'] = Path.get_tv_genres()
    else:
        context['loggedin'] = False

    context['is_staff'] = user.is_staff and 'true' or 'false'
    getLastWaiterStatus(context)

@check_force_password_change
@logAccessInfo
def home(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    context['greeting'] = siteGreeting and siteGreeting.greeting or 'Check out the new downloads!'
    context['active_page'] = 'home'
    files = File.objects.filter(hide=False).filter(finished=True).order_by('-id')[:10]
    context['files'] = files
    context['title'] = 'Home'
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, 'mediaviewer/home.html', context)

def getLastWaiterStatus(context):
    lastStatus = WaiterStatus.getLastStatus()
    context['waiterstatus'] = lastStatus and lastStatus.status or False
    context['waiterfailurereason'] = lastStatus and lastStatus.failureReason or ''

@logAccessInfo
def ajaxrunscraper(request):
    log.info("Running scraper")
    response = {'errmsg': ''}
    try:
        if request.user.is_staff:
            File.inferAllScrapers()
    except Exception, e:
        if DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'
    return HttpResponse(json.dumps(response), content_type='application/javascript')
