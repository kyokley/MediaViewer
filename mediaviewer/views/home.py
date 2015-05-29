from django.http import HttpResponse
from mediaviewer.models.usersettings import (
                                      DEFAULT_SITE_THEME,
                                      FILENAME_SORT,
                                      )
from mediaviewer.models.message import Message
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.waiterstatus import WaiterStatus
from django.shortcuts import render
from mediaviewer.models.file import File
from mediaviewer.utils import logAccessInfo
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
        context['site_theme'] = settings and settings.site_theme or DEFAULT_SITE_THEME
        context['default_sort'] = settings and settings.default_sort or FILENAME_SORT
        if includeMessages:
            for message in Message.getMessagesForUser(request.user):
                Message.add_message(request,
                        message.level,
                        message.body,
                        extra_tags=str(message.id))
    else:
        context['loggedin'] = False
        context['site_theme'] = DEFAULT_SITE_THEME

    context['is_staff'] = user.is_staff and 'true' or 'false'
    getLastWaiterStatus(context)

@logAccessInfo
def home(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    headers = generateHeader('home', request)
    context['greeting'] = siteGreeting and siteGreeting.greeting or 'Check out the new downloads!'
    context['header'] = headers[0]
    context['header2'] = headers[1]
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
    def __init__(self):
        self.homePage = '<li><a href="/mediaviewer/">Home</a></li>'
        self.activeHomePage = '<li class="active"><a href="/mediaviewer/">Home</a></li>'
        self.activeMoviesPage = '<li class="active"><a href="/mediaviewer/movies/display/0/">Movies</a></li>'
        self.moviesPage = '<li><a href="/mediaviewer/movies/display/0/">Movies</a></li>'

        self.activeTvshowsPage = '<li class="active"><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>'
        self.tvshowsPage = '<li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>'

        self.activeRequestsPage = '<li class="active"><a href="/mediaviewer/requests/">Requests</a></li>'
        self.requestsPage = '<li><a href="/mediaviewer/requests/">Requests</a></li>'

        self.activeDatausagePage = '<li class="active"><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>'
        self.datausagePage = '<li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>'

        self.activeUserusagePage = '<li class="active"><a href="/mediaviewer/userusage/">User Data Usage</a></li>'
        self.userusagePage = '<li><a href="/mediaviewer/userusage/">User Data Usage</a></li>'

        self.activeErrorsPage = '<li class="active"><a href="/mediaviewer/errors/display/50/">Errors</a></li>'
        self.errorsPage = '<li><a href="/mediaviewer/errors/display/50/">Errors</a></li>'
        self.disabledDatausagePage = ''
        self.disabledUserusagePage = ''
        self.disabledErrorsPage = '<li class="disabled"><a href="#">Errors</a></li>'

def generateHeader(page, request):
    if page == 'home':
        homePage = '<li class="active"><a href="/mediaviewer/">Home</a></li>'
    else:
        homePage = '<li><a href="/mediaviewer/">Home</a></li>'

    if page == 'movies':
        moviesPage = '<li class="active"><a href="/mediaviewer/movies/display/0/">Movies</a></li>'
    else:
        moviesPage = '<li><a href="/mediaviewer/movies/display/0/">Movies</a></li>'

    if page == 'tvshows':
        tvshowsPage = '<li class="active"><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>'
    else:
        tvshowsPage = '<li><a href="/mediaviewer/tvshows/summary/">TV Shows</a></li>'

    if page == 'requests':
        requestsPage = '<li class="active"><a href="/mediaviewer/requests/">Requests</a></li>'
    else:
        requestsPage = '<li><a href="/mediaviewer/requests/">Requests</a></li>'

    if request.user and request.user.is_staff:
        if page == 'datausage':
            datausagePage = '<li class="active"><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>'
        else:
            datausagePage = '<li><a href="/mediaviewer/datausage/display/50/">Data Usage</a></li>'

        if page == 'userusage':
            userusagePage = '<li class="active"><a href="/mediaviewer/userusage/">User Data Usage</a></li>'
        else:
            userusagePage = '<li><a href="/mediaviewer/userusage/">User Data Usage</a></li>'

        if page == 'errors':
            errorsPage = '<li class="active"><a href="/mediaviewer/errors/display/50/">Errors</a></li>'
        else:
            errorsPage = '<li><a href="/mediaviewer/errors/display/50/">Errors</a></li>'
    else:
        datausagePage = ''
        userusagePage = ''
        errorsPage = '<li class="disabled"><a href="#">Errors</a></li>'

    header = '''
                %(homePage)s
                %(moviesPage)s
                %(tvshowsPage)s
                %(requestsPage)s
    '''
    header2 = '''
        %(datausagePage)s
        %(userusagePage)s
        %(errorsPage)s
        '''
    params = {'homePage': homePage,
           'moviesPage': moviesPage,
           'tvshowsPage': tvshowsPage,
           'requestsPage': requestsPage,
           'datausagePage': datausagePage,
           'userusagePage': userusagePage,
           'errorsPage': errorsPage}
    header = header % params
    header2 = header2 % params
    return (mark_safe(header), mark_safe(header2))

@logAccessInfo
def ajaxrunscraper(request):
    log.info("Running scraper")
    response = {'errmsg': ''}
    try:
        File.inferAllScrapers()
    except Exception, e:
        if DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'
    return HttpResponse(json.dumps(response), mimetype='application/javascript')
