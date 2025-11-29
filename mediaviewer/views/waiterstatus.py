from __future__ import absolute_import

import json

import requests
from django.conf import settings
from django.http import HttpResponse

import logging

from mediaviewer.models.waiterstatus import WaiterStatus

log = logging.getLogger(__name__)


def ajaxwaiterstatus(request):
    try:
        resp = requests.get(
            settings.WAITER_STATUS_URL, timeout=settings.REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()

        log.debug(data)
        if "status" not in data or not data["status"]:
            failureReason = "Bad Symlink"
        else:
            failureReason = ""

        response = {
            "status": data.get("status", False),
            "failureReason": failureReason,
        }
    except Exception as e:
        response = {"status": False, "failureReason": "Timedout"}
        log.error(e)

    WaiterStatus.new(response["status"], response["failureReason"])

    return HttpResponse(json.dumps(response), content_type="application/javascript")
