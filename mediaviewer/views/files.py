from django.http import HttpResponse
from mediaviewer.models.file import File
from mediaviewer.views.home import setSiteWideContext
from django.contrib.auth.decorators import login_required
from mediaviewer.models.usersettings import (
                                      LOCAL_IP,
                                      BANGUP_IP,
                                      )
from mediaviewer.models.genre import Genre
from django.shortcuts import render
from mediaviewer.models.path import Path
from django.contrib.auth.models import User
from mediaviewer.models.message import Message
from django.contrib import messages
from mysite.settings import DEBUG
from mediaviewer.utils import logAccessInfo, check_force_password_change

import json
import re
ID_REGEX = re.compile('\d+')

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def files(request, items):
    user = request.user
    items = int(items)
    if items:
        files = File.objects.order_by('-id')[:items]
    else:
        files = File.objects.order_by('-id')
    for file in files:
        setattr(file, 'usercomment', file.usercomment(user))
    settings = user.settings()
    context = {
              'files': files,
              'items': items,
              'view': 'files',
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
               'can_download': settings and settings.can_download or False
              }
    context['active_page'] = 'files'
    context['title'] = 'Files'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/files.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def movies(request):
    user = request.user
    files = File.movies().filter(hide=False).order_by('-id')
    for file in files:
        setattr(file, 'usercomment', file.usercomment(user))
    settings = user.settings()
    context = {
              'files': files,
              'view': 'movies',
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
               'can_download': settings and settings.can_download or False
              }
    context['active_page'] = 'movies'
    context['title'] = 'Movies'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/files.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def movies_by_genre(request, genre_id):
    user = request.user
    # We're only interested in movies here so files must be defined
    ref_genre = Genre.objects.get(pk=genre_id)
    files = (File.objects.filter(_posterfile__genres=ref_genre)
                         .filter(hide=False)
                         .filter(path__is_movie=True))
    for file in files:
        setattr(file, 'usercomment', file.usercomment(user))
    settings = user.settings()
    context = {
              'files': files,
              'view': 'movies',
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
               'can_download': settings and settings.can_download or False
              }
    context['active_page'] = 'movies'
    context['title'] = 'Movies: {}'.format(ref_genre.genre)
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/files.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def tvshowsummary(request):
    pathDict = Path.distinctShowFolders()
    pathSet = [path for name, path in pathDict.items()]

    context = {'pathSet': pathSet}
    context['active_page'] = 'tvshows'
    context['title'] = 'TV Shows'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/tvsummary.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def tvshows_by_genre(request, genre_id):
    ref_genre = Genre.objects.get(pk=genre_id)
    pathDict = Path.distinctShowFoldersByGenre(ref_genre)
    pathSet = [path for name, path in pathDict.items()]

    context = {'pathSet': pathSet}
    context['active_page'] = 'tvshows'
    context['title'] = 'TV Shows: {}'.format(ref_genre.genre)
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/tvsummary.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def tvshows(request, pathid):
    user = request.user
    refpath = Path.objects.get(pk=pathid)
    files = File.objects.filter(path__localpathstr=refpath.localpathstr).filter(hide=False)
    for file in files:
        setattr(file, 'usercomment', file.usercomment(user))
    settings = user.settings()
    context = {
              'files': files,
              'path': refpath,
              'view': 'tvshows',
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
              'can_download': settings and settings.can_download or False
              }
    context['active_page'] = 'tvshows'
    context['title'] = refpath.displayName()
    context['long_plot'] = len(refpath.posterfile.plot) > 300
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/files.html', context)

@logAccessInfo
def ajaxreport(request):
    response = {'errmsg': ''}
    try:
        createdBy = request.user
        reportid = ID_REGEX.findall(request.POST['reportid'])[0]
        reportid = int(reportid)
        response['reportid'] = reportid
        file = File.objects.get(pk=reportid)
        users = User.objects.filter(is_staff=True)

        for user in users:
            Message.createNewMessage(user,
                                     '%s has been reported by %s' % (file.filename, createdBy.username),
                                     level=messages.WARNING)
    except Exception, e:
        if DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'
    return HttpResponse(json.dumps(response), content_type='application/javascript')
