from django.shortcuts import (
    get_object_or_404,
)
from datetime import datetime, timedelta
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.downloadtoken import DownloadToken
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.waiterstatus import WaiterStatus
from mediaviewer.models.genre import Genre

import json
import pytz

REWIND_THRESHOLD = 10  # in minutes


@csrf_exempt
def ajaxvideoprogress(request, guid, hashed_filename):
    data = {"offset": 0}
    dt = DownloadToken.getByGUID(guid)
    if not dt or not dt.user or not dt.isvalid:
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=412
        )

    user = dt.user

    if request.method == "GET":
        vp = VideoProgress.get(user, hashed_filename)
        if vp:
            offset = float(vp.offset)
            date_edited = vp.date_edited

            ref_time = datetime.now(pytz.timezone("utc")) - timedelta(
                minutes=REWIND_THRESHOLD
            )
            if date_edited < ref_time:
                offset = max(offset - 30, 0)

            data["offset"] = offset
            data["date_edited"] = date_edited.isoformat()
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=200
        )
    elif request.method == "POST":
        vp = VideoProgress.createOrUpdate(
            user,
            dt.filename,
            hashed_filename,
            request.POST["offset"],
            dt.file,
        )
        data["offset"] = float(vp.offset)
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=200
        )
    elif request.method == "DELETE":
        VideoProgress.destroy(user, hashed_filename)
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=204
        )
    else:
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=405
        )


@csrf_exempt
def ajaxgenres(request, guid):
    dt = DownloadToken.getByGUID(guid)
    if not dt or not dt.user or not dt.isvalid:
        return HttpResponse(None, content_type="application/json", status=412)

    if request.method == "GET":
        movie_genres = File.get_movie_genres()
        tv_genres = Path.get_tv_genres()
        data = {
            "movie_genres": [(mg.id, mg.genre) for mg in movie_genres],
            "tv_genres": [(mg.id, mg.genre) for mg in tv_genres],
        }
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=200
        )
    else:
        return HttpResponse(None, content_type="application/json", status=405)


def ajaxrows(request, qs):
    user = request.user

    settings = user.settings()
    can_download = settings.can_download

    lastStatus = WaiterStatus.getLastStatus()
    waiterstatus = lastStatus.status if lastStatus else False

    request_params = dict(request.GET)
    offset = int(request_params['start'][0])
    length = int(request_params['length'][0])
    search_str = request_params['search[value]'][0]
    draw = int(request_params['draw'][0])

    qs = qs.search(search_str)
    files = qs[offset:offset + length]

    viewed_by_file = UserComment.objects.viewed_by_file(user)
    file_data = [file.ajax_row_payload(can_download,
                                       waiterstatus,
                                       viewed_by_file,
                                       ) for file in files]

    payload = {
        'draw': draw,
        "recordsTotal": File.movies_ordered_by_id().count(),
        "recordsFiltered": qs.count(),
        "data": file_data
    }

    return HttpResponse(
        json.dumps(payload), content_type="application/json", status=200
    )

@csrf_exempt
def ajaxmovierows(request):
    qs = File.movies_ordered_by_id()
    return ajaxrows(request, qs)


@csrf_exempt
def ajaxfilesrows(request):
    qs = File.objects.order_by('-id')
    return ajaxrows(request, qs)


@csrf_exempt
def ajaxmoviesbygenrerows(request, genre_id):
    genre = get_object_or_404(Genre, pk=genre_id)
    qs = File.movies_by_genre(genre).order_by('-id')
    return ajaxrows(request, qs)
