from django.shortcuts import render
from mediaviewer.views.home import generateHeader, setSiteWideContext
from django.contrib.auth import logout
from mediaviewer.utils import logAccessInfo

@logAccessInfo
def signout(request):
    logout(request)
    context = {}
    context['header'] = generateHeader('logout', request)
    context['loggedin'] = False
    context['title'] = 'Signed out'
    setSiteWideContext(context, request)
    return render(request, 'mediaviewer/logout.html', context)

