from mediaviewer.views.views_utils import setSiteWideContext
from django.shortcuts import render, get_object_or_404
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.password_reset import check_force_password_change
from mediaviewer.models.file import File
from mediaviewer.models.downloadtoken import DownloadToken


@check_force_password_change
@logAccessInfo
def waiter_display(request, fileid):
    context = {}
    context['active_page'] = 'home'
    context['title'] = 'Home'
    file = get_object_or_404(File, pk=fileid)
    user = request.user

    if not user.is_authenticated():
        context['errmsg'] = 'User not authenticated. Refresh and try again.'
    else:
        dt = DownloadToken.new(user, file)

        downloadlink = file.downloadLink(user, dt.guid)
        context.update({'guid': dt.guid,
                        'isMovie': dt.ismovie,
                        'downloadLink': downloadlink,
                        'errmsg': ''})
    setSiteWideContext(context, request, includeMessages=False)

    return render(request, 'mediaviewer/waiter_display.html', context)
