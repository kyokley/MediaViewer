from django.shortcuts import render
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth import logout
from mediaviewer.utils import logAccessInfo


@logAccessInfo
def signout(request):
    logout(request)
    context = {}
    context['active_page'] = 'logout'
    context['loggedin'] = False
    context['title'] = 'Signed out'
    setSiteWideContext(context, request)
    return render(request, 'mediaviewer/logout.html', context)
