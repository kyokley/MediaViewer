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

    if request.user and request.user.is_staff:
        if page == 'datausage':
            datausagePage = headers.activeDatausagePage()
        else:
            datausagePage = headers.datausagePage()

        if page == 'userusage':
            userusagePage = headers.activeUserusagePage()
        else:
            userusagePage = headers.userusagePage()

        if page == 'errors':
            errorsPage = headers.activeErrorsPage()
        else:
            errorsPage = headers.errorsPage()
    else:
        datausagePage = ''
        userusagePage = ''
        errorsPage = headers.disabledErrorsPage()

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
