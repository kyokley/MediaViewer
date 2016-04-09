from __future__ import absolute_import
from django.http import HttpResponse
from mysite.settings import (
                             WAITER_STATUS_URL,
                             REQUEST_TIMEOUT,
                             )
from mediaviewer.models.waiterstatus import WaiterStatus
from datetime import datetime as dateObj
from django.utils.timezone import utc

import json
import requests
from mediaviewer.log import log

def ajaxwaiterstatus(request):
    try:
        resp = requests.get(WAITER_STATUS_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        log.debug(data)
        if 'status' not in data or not data['status']:
            if 'sql_status' not in data or not data['sql_status']:
                failureReason = 'Expired SQL Connection'
            else:
                failureReason = 'Bad Symlink'
        else:
            failureReason = ''

        response = {'status': data['status'], 'failureReason': failureReason}
    except Exception, e:
        response = {'status': False, 'failureReason': 'Timedout'}
        print e
    newStatus = WaiterStatus()
    newStatus.status = response['status']
    newStatus.failureReason = response['failureReason']
    newStatus.datecreated = dateObj.utcnow().replace(tzinfo=utc)
    newStatus.save()

    return HttpResponse(json.dumps(response), mimetype='application/javascript')

