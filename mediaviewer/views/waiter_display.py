from mediaviewer.views.home import setSiteWideContext
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo, check_force_password_change
from mediaviewer.models.file import File
from mediaviewer.models.downloadtoken import DownloadToken


@check_force_password_change
@logAccessInfo
def waiter_display(request, fileid):
    context = {}
    context['active_page'] = 'home'
    context['title'] = 'Home'
    file = File.objects.get(pk=fileid)
    user = request.user

    if not user.is_authenticated():
        context['errmsg'] = 'User not authenticated. Refresh and try again.'
    elif file and user:
        dt = DownloadToken.new(user, file)

        downloadlink = file.downloadLink(user, dt.guid)
        context.update({'guid': dt.guid,
                        'isMovie': dt.ismovie,
                        'downloadLink': downloadlink,
                        'errmsg': ''})
    else:
        context['errmsg'] = 'An error has occurred'
    setSiteWideContext(context, request, includeMessages=False)

    return render(request, 'mediaviewer/waiter_display.html', context)
