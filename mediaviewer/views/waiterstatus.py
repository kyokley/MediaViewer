from django.http import HttpResponse
from site.settings import (
                             WAITER_STATUS_URL,
                             )
from mediaviewer.models.waiterstatus import WaiterStatus
from datetime import datetime as dateObj
from django.utils.timezone import utc

import json
import urllib2
from mediaviewer.log import log

def ajaxwaiterstatus(request):
    try:
        url = urllib2.urlopen(WAITER_STATUS_URL, timeout=2)
        data = json.load(url)

        log.debug(url.read())
        log.debug(data)
        if not data['status']:
            if not data['sql_status']:
                failureReason = 'Expired SQL Connection'
            else:
                failureReason = 'Bad Symlink'
        else:
            failureReason = ''

        response = {'status': data['status'], 'failureReason': failureReason}
        url.close()
    except Exception, e:
        response = {'status': False, 'failureReason': 'Timedout'}
        print e
    newStatus = WaiterStatus()
    newStatus.status = response['status']
    newStatus.failureReason = response['failureReason']
    newStatus.datecreated = dateObj.utcnow().replace(tzinfo=utc)
    newStatus.save()

    return HttpResponse(json.dumps(response), mimetype='application/javascript')

