from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.downloadtoken import DownloadToken
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import json

@csrf_exempt
def ajaxvideoprogress(request, guid, filename):
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
        vp = VideoProgress.get(user, filename)
        if vp:
            data['offset'] = float(vp.offset)
            data['date_edited'] = vp.date_edited
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=200)
    elif request.method == 'POST':
        vp = VideoProgress.createOrUpdate(user,
                                          filename,
                                          request.POST['offset'])
        data['offset'] = float(vp.offset)
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=200)
    elif request.method == 'DELETE':
        VideoProgress.delete(user, filename)
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=204)
    else:
        return HttpResponse(json.dumps(data),
                            content_type='application/json',
                            status=405)
