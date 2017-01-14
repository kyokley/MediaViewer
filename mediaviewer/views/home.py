from django.http import HttpResponse
from mediaviewer.models.usersettings import (
                                      FILENAME_SORT,
                                      )
from mediaviewer.models.message import Message
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.waiterstatus import WaiterStatus
from django.shortcuts import render
from mediaviewer.models.file import File
from mediaviewer.utils import logAccessInfo, check_force_password_change
from django.utils.safestring import mark_safe
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
            for message in Message.getMessagesForUser(request.user):
                Message.add_message(request,
                        message.level,
                        message.body,
                        extra_tags=str(message.id))
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
    context['header'] = generateHeader('home', request)
    files = File.objects.filter(hide=False).filter(finished=True).order_by('-id')[:10]
    context['files'] = files
    context['title'] = 'Home'
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, 'mediaviewer/home.html', context)

def getLastWaiterStatus(context):
    lastStatus = WaiterStatus.getLastStatus()
    context['waiterstatus'] = lastStatus and lastStatus.status or False
    context['waiterfailurereason'] = lastStatus and lastStatus.failureReason or ''

class HeaderHelper(object):
    #TODO: Remove ALL of this html and relocate to templates!

    def homePage(self):
        return '<li><a href="/mediaviewer/">Home</a></li>'

    def activeHomePage(self):
        return '<li class="active"><a href="/mediaviewer/">Home</a></li>'

    def activeMoviesPage(self):
        return '<li class="active"><a href="/mediaviewer/movies/display/0/">Movies</a></li>'

    def moviesPage(self):
        return '<li><a href="/mediaviewer/movies/display/0/">Movies</a></li>'

    def activeTvshowsPage(self):
        return '<li class="active"><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>'

    def tvshowsPage(self):
        return '<li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>'

    def activeRequestsPage(self):
        return '<li class="active"><a href="/mediaviewer/requests/">Requests</a></li>'

    def requestsPage(self):
        return '<li><a href="/mediaviewer/requests/">Requests</a></li>'

    def activeDatausagePage(self):
        return '<li class="active"><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>'

    def datausagePage(self):
        return '<li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>'

    def activeUserusagePage(self):
        return '<li class="active"><a href="/mediaviewer/userusage/">User Data Usage</a></li>'

    def userusagePage(self):
        return '<li><a href="/mediaviewer/userusage/">User Data Usage</a></li>'

    def activeErrorsPage(self):
        return '<li class="active"><a href="/mediaviewer/errors/display/50/">Errors</a></li>'

    def errorsPage(self):
        return '<li><a href="/mediaviewer/errors/display/50/">Errors</a></li>'

    def disabledDatausagePage(self):
        return ''

    def disabledUserusagePage(self):
        return ''

    def disabledErrorsPage(self):
        return '<li class="disabled"><a href="#">Errors</a></li>'

def generateHeader(page, request):
    headers = HeaderHelper()

    if page == 'home':
        homePage = headers.activeHomePage()
    else:
        homePage = headers.homePage()

    if page == 'movies':
        moviesPage = headers.activeMoviesPage()
    else:
        moviesPage = headers.moviesPage()

    if page == 'tvshows':
        tvshowsPage = headers.activeTvshowsPage()
    else:
        tvshowsPage = headers.tvshowsPage()

    if page == 'requests':
        requestsPage = headers.activeRequestsPage()
    else:
        requestsPage = headers.requestsPage()

    header = '''
                %(homePage)s
                %(moviesPage)s
                %(tvshowsPage)s
                %(requestsPage)s
    '''
    params = {'homePage': homePage,
              'moviesPage': moviesPage,
              'tvshowsPage': tvshowsPage,
              'requestsPage': requestsPage,
              }
    header = header % params
    return mark_safe(header) #nosec

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
