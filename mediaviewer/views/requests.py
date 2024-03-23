import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from mediaviewer import interjections
from mediaviewer.models.message import Message
from mediaviewer.models.request import Request, RequestVote
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def requests(request):
    items = Request.objects.filter(done=False)
    user = request.user

    # The purpose of the code below is to put the item in a user "context"
    # This is required to use the item in django's templating language
    # It may be smarter to create a new type of object for this purpose
    for item in items:
        setattr(item, "canVote", item.canVote(user))
    context = {
        "items": items,
        "user": user,
    }
    context["active_page"] = "requests"
    context["title"] = "Requests"
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/request.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def addrequests(request):
    name = request.POST["newrequest"]

    try:
        if name:
            newrequest = Request.new(name, request.user)
            if newrequest.canVote(request.user):
                RequestVote.new(newrequest, request.user)

            createdBy = request.user
            users = User.objects.filter(is_staff=True)

            for user in users:
                Message.createNewMessage(
                    user,
                    f"{newrequest.name} has been requested by {createdBy.username}",
                    level=messages.INFO,
                )
    except Exception as e:
        print(e)
        return render(
            request,
            "mediaviewer/request.html",
            {"error_message": "An error has occurred"},
        )
    else:
        return HttpResponseRedirect(reverse("mediaviewer:requests"))


@logAccessInfo
def ajaxvote(request):
    requestid = int(request.POST["requestid"])
    requestObj = get_object_or_404(Request, pk=requestid)

    user = request.user
    if not user.is_authenticated:
        raise Exception("User not authenticated. Refresh and try again.")

    RequestVote.new(requestObj, user)

    response = {}
    response["numberOfVotes"] = requestObj.numberOfVotes()
    response["requestid"] = requestid

    return HttpResponse(json.dumps(response), content_type="application/javascript")


@logAccessInfo
def ajaxdone(request):
    requestid = int(request.POST["requestid"])
    requestObj = get_object_or_404(Request, pk=requestid)

    response = {"errmsg": ""}

    user = request.user
    if not user.is_authenticated:
        response["errmsg"] = "User not authenticated. Refresh and try again."
        return HttpResponse(json.dumps(response), content_type="application/javascript")
    elif not user.is_staff:
        response["errmsg"] = "User is not a staffer"
        return HttpResponse(json.dumps(response), content_type="application/javascript")

    done = True

    requestObj.done = done
    requestObj.save()

    response["message"] = "Marked done!"
    response["requestid"] = requestid

    try:
        notifyUsers = requestObj.getSupportingUsers()
        for notifyUser in notifyUsers:
            interjection = interjections.getInterjection()
            Message.createNewMessage(
                notifyUser,
                f"{interjection} Request for {requestObj.name} is complete!",
                level=Message.SUCCESS,
            )
    except Exception as e:
        if settings.DEBUG:
            response["errmsg"] = str(e)
        else:
            response["errmsg"] = "An error has occurred"

    return HttpResponse(json.dumps(response), content_type="application/javascript")


@logAccessInfo
def ajaxgiveup(request):
    requestid = int(request.POST["requestid"])
    requestObj = get_object_or_404(Request, pk=requestid)

    response = {"errmsg": ""}

    user = request.user
    if not user.is_authenticated:
        response["errmsg"] = "User not authenticated. Refresh and try again."
        return HttpResponse(json.dumps(response), content_type="application/javascript")
    elif not user.is_staff:
        response["errmsg"] = "User is not a staffer"
        return HttpResponse(json.dumps(response), content_type="application/javascript")

    requestObj.done = True
    requestObj.save()

    response["message"] = "Give up!"
    response["requestid"] = requestid

    try:
        notifyUsers = requestObj.getSupportingUsers()
        for notifyUser in notifyUsers:
            interjection = interjections.getFailures()
            Message.createNewMessage(
                notifyUser,
                f"{interjection} I couldn't find {requestObj.name}",
                level=Message.ERROR,
            )
    except Exception as e:
        if settings.DEBUG:
            response["errmsg"] = str(e)
        else:
            response["errmsg"] = "An error has occurred"

    return HttpResponse(json.dumps(response), content_type="application/javascript")
