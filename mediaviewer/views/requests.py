from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from mediaviewer.models.request import (Request,
                                        RequestVote,
                                        )
from mediaviewer.models.message import Message
from mediaviewer.views.home import setSiteWideContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from mysite.settings import DEBUG
from mediaviewer.utils import logAccessInfo, check_force_password_change

import json
from mediaviewer import interjections

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def requests(request):
    items = Request.objects.filter(done=False)
    user = request.user
    for item in items:
        setattr(item, 'canVote', item.canVote(user))
    context = {'items': items,
               'user': user,
               }
    context['active_page'] = 'requests'
    context['title'] = 'Requests'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/request.html', context)

@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def addrequests(request):
    name = request.POST['newrequest']

    try:
        if name:
            newrequest = Request.new(name, request.user)
            RequestVote.new(newrequest, request.user)

            createdBy = request.user
            users = User.objects.filter(is_staff=True)

            for user in users:
                Message.createNewMessage(user,
                                         '%s has been requested by %s' % (name, createdBy.username),
                                         level=messages.INFO)
    except Exception, e:
        print e
        return render(request, 'mediaviewer/request.html',
                {'error_message': 'An error has occurred',})
    else:
        return HttpResponseRedirect(reverse('mediaviewer:requests'))

@logAccessInfo
def ajaxvote(request):
    requestid = int(request.POST['requestid'])
    requestObj = get_object_or_404(Request, pk=requestid)

    user = request.user
    if not user.is_authenticated():
        raise Exception("User not authenticated. Refresh and try again.")

    RequestVote.new(requestObj, user)

    response = {}
    response['numberOfVotes'] = requestObj.numberOfVotes()
    response['requestid'] = requestid

    return HttpResponse(json.dumps(response), content_type='application/javascript')

@logAccessInfo
def ajaxdone(request):
    requestid = int(request.POST['requestid'])
    requestObj = get_object_or_404(Request, pk=requestid)

    response = {'errmsg': ''}

    user = request.user
    if not user.is_authenticated():
        response['errmsg'] = 'User not authenticated. Refresh and try again.'
        return HttpResponse(json.dumps(response), content_type='application/javascript')
    elif not user or not user.is_staff:
        response['errmsg'] = 'User is not a staffer'
        return HttpResponse(json.dumps(response), content_type='application/javascript')

    done = True

    requestObj.done = done
    requestObj.save()

    response['message'] = "Marked done!"
    response['requestid'] = requestid

    try:
        notifyUsers = requestObj.getSupportingUsers()
        for notifyUser in notifyUsers:
            interjection = interjections.getInterjection()
            Message.createNewMessage(notifyUser, "%s Request for %s is complete!" % (interjection, requestObj.name), level=Message.SUCCESS)
    except Exception, e:
        if DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'

    return HttpResponse(json.dumps(response), content_type='application/javascript')

@logAccessInfo
def ajaxgiveup(request):
    requestid = int(request.POST['requestid'])
    requestObj = get_object_or_404(Request, pk=requestid)

    response = {'errmsg': ''}

    user = request.user
    if not user.is_authenticated():
        response['errmsg'] = 'User not authenticated. Refresh and try again.'
        return HttpResponse(json.dumps(response), content_type='application/javascript')
    elif not user or not user.is_staff:
        response['errmsg'] = 'User is not a staffer'
        return HttpResponse(json.dumps(response), content_type='application/javascript')

    requestObj.done = True
    requestObj.save()

    response['message'] = "Give up!"
    response['requestid'] = requestid

    try:
        notifyUsers = requestObj.getSupportingUsers()
        for notifyUser in notifyUsers:
            interjection = interjections.getFailures()
            Message.createNewMessage(notifyUser, "%s I couldn't find %s" % (interjection, requestObj.name), level=Message.ERROR)
    except Exception, e:
        if DEBUG:
            response['errmsg'] = str(e)
        else:
            response['errmsg'] = 'An error has occurred'

    return HttpResponse(json.dumps(response), content_type='application/javascript')
