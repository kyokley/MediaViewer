from django.contrib.auth.decorators import login_required
from mediaviewer.models.downloadclick import DownloadClick
from mediaviewer.views.home import generateHeader, setSiteWideContext
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo, check_force_password_change

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def userusage(request):
    downloadclicks = DownloadClick.objects.order_by('-id')
    context = {
              'userusage': downloadclicks,
              'view': 'userusage',
              }
    context['header'] = generateHeader('userusage', request)
    context['title'] = 'User Usage'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/userusage.html', context)

