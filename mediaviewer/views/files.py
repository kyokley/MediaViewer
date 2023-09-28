from django.http import HttpResponse, Http404
from django.shortcuts import (
    get_object_or_404,
)

from mediaviewer.models.file import File
from django.contrib.auth.models import User
from mediaviewer.models.message import Message
from django.contrib import messages
from django.conf import settings
from mediaviewer.utils import logAccessInfo

import json
import re

ID_REGEX = re.compile(r"\d+")


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
