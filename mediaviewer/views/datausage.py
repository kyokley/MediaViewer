from django.contrib.auth.decorators import login_required
from mediaviewer.models.datatransmission import DataTransmission
from mediaviewer.views.home import generateHeader, setSiteWideContext
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo, check_force_password_change

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def datausage(request, items):
    items = int(items)
    if items:
        datausage = DataTransmission.objects.order_by('-id')[:items]
    else:
        datausage = DataTransmission.objects.order_by('-id')
    context = {
              'datausage': datausage,
              'view': 'datausage',
              }
    context['header'] = generateHeader('datausage', request)
    context['title'] = 'Data Usage'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/datausage.html', context)

