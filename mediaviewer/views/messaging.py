from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from mediaviewer.views.home import generateHeader, setSiteWideContext
from mediaviewer.models.message import Message
from django.shortcuts import render
from mysite.settings import DEBUG
from mediaviewer.utils import logAccessInfo

import json
import re
ID_REGEX = re.compile('\d+')

@login_required(login_url='/mediaviewer/login/')
@logAccessInfo
def submitsitewidemessage(request):
    user = request.user
    context = {}
    headers = generateHeader('submitsitewidemessage', request)
    context['header'] = headers[0]
    context['header2'] = headers[1]
    setSiteWideContext(context, request)

    message = request.POST.get('sitemessage')
    level = Message.levelDict[request.POST.get('level')]

    if user.is_staff:
        Message.createSitewideMessage(message, level=level)
    else:
        raise Exception("User is not a staffer!")
    return render(request, 'mediaviewer/settingsresults.html', context)

@logAccessInfo
def ajaxclosemessage(request):
    response = {'errmsg': ''}
    try:
        messageid = ID_REGEX.findall(request.POST['messageid'])[0]
        messageid = int(messageid)
        message = Message.objects.filter(pk=messageid)
        message = message and message[0]
        user = request.user

        if not user.is_authenticated():
            response = {'errmsg': 'User not authenticated'}
        elif message and user:
            message.sent = True
            message.save()
    except Exception, e:
        if DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'

    return HttpResponse(json.dumps(response), mimetype='application/javascript')
