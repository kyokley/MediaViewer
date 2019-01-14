from __future__ import absolute_import
from django.http import HttpResponse
from django.conf import settings
from mediaviewer.models.waiterstatus import WaiterStatus

import json
import requests
from mediaviewer.log import log


def ajaxwaiterstatus(request):
    try:
        resp = requests.get(settings.WAITER_STATUS_URL,
                            timeout=settings.REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        log.debug(data)
        if 'status' not in data or not data['status']:
            failureReason = 'Bad Symlink'
        else:
            failureReason = ''

        response = {'status': data.get('status', False),
                    u'failureReason': failureReason}
    except Exception as e:
        response = {'status': False, 'failureReason': 'Timedout'}
        log.error(e)

    WaiterStatus.new(response['status'],
                     response['failureReason'])

    return HttpResponse(json.dumps(response),
                        content_type='application/javascript')
