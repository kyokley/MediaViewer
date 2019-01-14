import json

from django.http import HttpResponse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render
from mediaviewer.models.file import File
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.password_reset import check_force_password_change
from mediaviewer.views.views_utils import setSiteWideContext
from django.conf import settings

from mediaviewer.log import log


@check_force_password_change
@logAccessInfo
def home(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    context['greeting'] = (siteGreeting and
                           siteGreeting.greeting or
                           'Check out the new downloads!')
    context['active_page'] = 'home'
    files = File.most_recent_files()
    context['files'] = files
    context['title'] = 'Home'
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, 'mediaviewer/home.html', context)


@logAccessInfo
def ajaxrunscraper(request):
    log.info("Running scraper")
    response = {'errmsg': ''}
    try:
        if request.user.is_staff:
            File.inferAllScrapers()
    except Exception as e:
        if settings.DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'
    return HttpResponse(json.dumps(response),
                        content_type='application/javascript')
