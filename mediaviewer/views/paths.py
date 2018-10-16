from django.contrib.auth.decorators import login_required
from mediaviewer.models.path import Path
from mediaviewer.views.views_utils import setSiteWideContext
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.password_reset import check_force_password_change


@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def paths(request, items):
    items = int(items)
    if items:
        paths = Path.objects.order_by('-id')[:items]
    else:
        paths = Path.objects.order_by('-id')
    context = {
              'paths': paths,
              'view': 'paths',
              }
    context['active_page'] = 'paths'
    context['title'] = 'Paths'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/paths.html', context)
