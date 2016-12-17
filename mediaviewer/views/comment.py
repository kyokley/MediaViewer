from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.file import File
from django.contrib.auth.decorators import login_required
from mediaviewer.models.usersettings import (
                                      LOCAL_IP,
                                      BANGUP_IP,
                                      )
from django.core.urlresolvers import reverse
from mediaviewer.views.home import generateHeader, setSiteWideContext
from mediaviewer.utils import logAccessInfo, check_force_password_change

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def comment(request, file_id):
    file = get_object_or_404(File, pk=file_id)
    try:
        comment = request.POST.get('comment')
        viewed = request.POST.get('viewed') == 'true' and True or False
        usercomment = file.usercomment(request.user)
        if usercomment:
            usercomment.comment = comment
            usercomment.viewed = viewed
        else:
            UserComment.new(file,
                            request.user,
                            comment,
                            viewed)

        if request.user.is_staff:
            if (file._searchString != request.POST.get('search', file._searchString) or
                    file.imdb_id != request.POST.get('imdb_id', file.imdb_id) or
                    file.override_filename != request.POST.get('episode_name', file.override_filename) or
                    file.override_season != request.POST.get('season', file.override_season) or
                    file.override_episode != request.POST.get('episode_number', file.override_episode)):
                file.posterfile.delete()
                if file.path.posterfile:
                    file.path.posterfile.delete()
                file._searchString = request.POST.get('search', file._searchString)
                file.imdb_id = request.POST.get('imdb_id', file.imdb_id)
                file.override_filename = request.POST.get('episode_name', file.override_filename)
                file.override_season = request.POST.get('season', file.override_season)
                file.override_episode = request.POST.get('episode_number', file.override_episode)

            file.hide = request.POST.get('hidden', file.hide) == 'true' or False
            file.save()

    except Exception:
        return render(request, 'mediaviewer/filesdetail.html',
                {'file': file,
                 'error_message': 'An error has occurred',})
    else:
        return HttpResponseRedirect(reverse('mediaviewer:results', args=(file.id,)))

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def results(request, file_id):
    file = File.objects.get(pk=file_id)
    context = {'file': file,
              'LOCAL_IP': LOCAL_IP,
              'BANGUP_IP': BANGUP_IP,
               'can_download': request.user.settings() and request.user.settings().can_download or False
            }
    context['header'] = generateHeader('results', request)
    context['title'] = 'Saved Successfully!'
    setSiteWideContext(context, request)
    return render(request, 'mediaviewer/filesresults.html', context)
