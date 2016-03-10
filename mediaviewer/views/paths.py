from django.contrib.auth.decorators import login_required
from mediaviewer.models.path import Path
from mediaviewer.views.home import generateHeader, setSiteWideContext
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo

@login_required(login_url='/mediaviewer/login/')
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
    context['header'] = generateHeader('paths', request)
    context['title'] = 'Paths'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/paths.html', context)

