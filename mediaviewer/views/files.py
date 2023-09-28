from django.http import HttpResponse, Http404
from django.shortcuts import (
    render,
    get_object_or_404,
)

from mediaviewer.models.file import File
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth.decorators import login_required
from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)
from django.contrib.auth.models import User
from mediaviewer.models.message import Message
from django.contrib import messages
from django.conf import settings
from mediaviewer.utils import logAccessInfo

import json
import re

ID_REGEX = re.compile(r"\d+")


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def files(request, items):
    user = request.user
    items = int(items)
    if items:
        files = File.objects.order_by("-id")[:items]
    else:
        files = File.objects.order_by("-id")
    files = files.select_related("path")

    settings = user.settings()
    context = {
        "items": items,
        "view": "files",
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "can_download": (settings and settings.can_download or False),
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "ajaxfilesrows",
    }
    context["active_page"] = "files"
    context["title"] = "Files"
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/files.html", context)


@logAccessInfo
def ajaxreport(request):
    response = {"errmsg": ""}
    try:
        createdBy = request.user
        reportid = ID_REGEX.findall(request.POST["reportid"])[0]
        reportid = int(reportid)
        response["reportid"] = reportid
        file = get_object_or_404(File, pk=reportid)
        users = User.objects.filter(is_staff=True)

        for user in users:
            Message.createNewMessage(
                user,
                f"{file.filename} has been reported by {createdBy.username}",
                level=messages.WARNING,
            )
    except Http404:
        raise
    except Exception as e:
        if settings.DEBUG:
            response["errmsg"] = str(e)
        else:
            response["errmsg"] = "An error has occurred"
    return HttpResponse(json.dumps(response), content_type="application/javascript")
