from datetime import datetime, timedelta
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.downloadtoken import DownloadToken
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import json
import pytz

REWIND_THRESHOLD = 10 # in minutes

@csrf_exempt
def ajaxvideoprogress(request, guid, hashed_filename):
    data = {'offset': 0}
    dt = DownloadToken.getByGUID(guid)
    if (not dt or
            not dt.user or
            not dt.isvalid):
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=412)

    user = dt.user

    if request.method == 'GET':
        vp = VideoProgress.get(user, hashed_filename)
        if vp:
            offset = float(vp.offset)
            date_edited = vp.date_edited

            ref_time = datetime.now(pytz.timezone('utc')) - timedelta(minutes=REWIND_THRESHOLD)
            if date_edited < ref_time:
                offset = max(offset - 30, 0)

            data['offset'] = offset
            data['date_edited'] = date_edited.isoformat()
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=200)
    elif request.method == 'POST':
        vp = VideoProgress.createOrUpdate(user,
                                          dt.filename,
                                          hashed_filename,
                                          request.POST['offset'],
                                          dt.file,
                                          )
        data['offset'] = float(vp.offset)
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=200)
    elif request.method == 'DELETE':
        VideoProgress.delete(user, hashed_filename)
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=204)
    else:
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=405)
