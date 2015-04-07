from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.file import File
from django.contrib.auth.decorators import login_required
from datetime import datetime as dateObj
from django.utils.timezone import utc
from mediaviewer.models.usersettings import (
                                      LOCAL_IP,
                                      BANGUP_IP,
                                      )
from django.core.urlresolvers import reverse
from mediaviewer.views.home import generateHeader, setSiteWideContext
from mediaviewer.utils import logAccessInfo

@login_required(login_url='/mediaviewer/login/')
@logAccessInfo
def comment(request, file_id):
    file = get_object_or_404(File, pk=file_id)
    changed = False
    try:
        comment = request.POST['comment']
        viewed = request.POST['viewed'] == 'true' and True or False
        usercomment = file.usercomment(request.user)
        if usercomment:
            changed = usercomment.comment != comment
            changed = usercomment.viewed != viewed or changed
            usercomment.comment = comment
            usercomment.viewed = viewed
        else:
            usercomment = UserComment()
            usercomment.file = file
            usercomment.user = request.user
            usercomment.comment = comment
            usercomment.viewed = viewed
            usercomment.datecreated = dateObj.utcnow().replace(tzinfo=utc)
            changed = True

        if request.user.is_staff:
            if file._searchString != request.POST['search'] or file.imdb_id != request.POST['imdb_id']:
                file.posterfile.delete()
                if file.path.posterfile:
                    file.path.posterfile.delete()
                file._searchString = request.POST['search']
                file.imdb_id = request.POST['imdb_id']

            file.hide = request.POST['hidden'] == 'true' or False

        if changed:
            file.dateedited = dateObj.utcnow().replace(tzinfo=utc)
            usercomment.dateedited = dateObj.utcnow().replace(tzinfo=utc)

        file.save()
        usercomment.save()
    except Exception, e:
        print e
        return render(request, 'mediaviewer/filesdetail.html',
                {'file': file,
                 'error_message': 'An error has occurred',})
    else:
        return HttpResponseRedirect(reverse('mediaviewer:results', args=(file.id,)))

@login_required(login_url='/mediaviewer/login/')
@logAccessInfo
def results(request, file_id):
    file = File.objects.get(pk=file_id)
    context = {'file': file,
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
               'can_download': request.user.settings() and request.user.settings().can_download or False
            }
    headers = generateHeader('results', request)
    context['header'] = headers[0]
    context['header2'] = headers[1]
    context['title'] = 'Saved Successfully!'
    setSiteWideContext(context, request)
    return render(request, 'mediaviewer/filesresults.html', context)

