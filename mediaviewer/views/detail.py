from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.views.home import setSiteWideContext
from mediaviewer.models.usersettings import (LOCAL_IP,
                                             BANGUP_IP,
                                             )
from mediaviewer.utils import logAccessInfo, humansize, check_force_password_change
from django.shortcuts import render, get_object_or_404
import json

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def filesdetail(request, file_id):
    user = request.user
    file = File.objects.get(pk=file_id)
    skip = file.skip and True or False
    finished = file.finished and True or False
    usercomment = file.usercomment(user)
    if usercomment:
        viewed = usercomment.viewed and True or False
        comment = bool(usercomment.comment) and usercomment.comment or ""
        setattr(file, 'usercomment', usercomment)
    else:
        viewed = False
        comment = ''

    posterfile = file.posterfile

    settings = user.settings()
    context = {'file': file,
               'posterfile': posterfile,
               'comment': comment,
               'skip': skip,
               'finished': finished,
               'LOCAL_IP': LOCAL_IP,
               'BANGUP_IP': BANGUP_IP,
               'viewed': viewed,
               'can_download': settings and settings.can_download or False,
               'file_size': file.size and humansize(file.size)}
    context['active_page'] = 'filesdetail'
    context['title'] = file.isMovie() and file.rawSearchString() or file.path.displayName()
    setSiteWideContext(context, request)
    return render(request, 'mediaviewer/filesdetail.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def pathsdetail(request, path_id):
    path = Path.objects.get(pk=path_id)
    context = {'path': path}
    context['active_page'] = 'pathsdetail'
    context['title'] = path.displayName()
    setSiteWideContext(context, request)
    return render(request, 'mediaviewer/pathsdetail.html', context)

@logAccessInfo
def ajaxviewed(request):
    fileid = int(request.POST['fileid'])
    viewed = request.POST['viewed'] == 'true' and True or False
    file = get_object_or_404(File, pk=fileid)
    response = {'errmsg':''}

    errmsg = ""

    user = request.user
    if not user.is_authenticated():
        errmsg = "User not authenticated. Refresh and try again."
    if not user:
        errmsg = "An error has occurred"

    if errmsg:
        response['errmsg'] = errmsg
        return HttpResponse(json.dumps(response), content_type='application/javascript')

    file.markFileViewed(user, viewed)

    response['fileid'] = fileid
    response['viewed'] = viewed

    return HttpResponse(json.dumps(response), content_type='application/javascript')

@csrf_exempt
def ajaxsuperviewed(request):
    errmsg = ''
    guid = request.POST['guid']
    viewed = request.POST['viewed'] == 'True' and True or False

    if viewed:
        token = (DownloadToken.objects
                              .filter(guid=guid)
                              .first())
        if token and token.isvalid:
            token.file.markFileViewed(token.user, viewed)
        else:
            errmsg = 'Token is invalid'

    response = {'errmsg': errmsg,
                'guid': guid,
                'viewed': viewed}
    response = json.dumps(response)
    return HttpResponse(response, content_type="application/json")

@logAccessInfo
def ajaxdownloadbutton(request):
    response = {'errmsg': ''}
    fileid = int(request.POST['fileid'])
    file = File.objects.get(pk=fileid)
    user = request.user

    if not user.is_authenticated():
        response = {'errmsg': 'User not authenticated. Refresh and try again.'}
    elif file and user:
        dt = DownloadToken.new(user, file)

        downloadlink = file.downloadLink(user, dt.guid)
        response = {'guid': dt.guid,
                    'isMovie': dt.ismovie,
                    'downloadLink': downloadlink,
                    'errmsg': ''}
    else:
        response = {'errmsg': 'An error has occurred'}

    return HttpResponse(json.dumps(response), content_type='application/javascript')
