from django.shortcuts import get_object_or_404
from django.db import models
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


def _ajax_file_rows(request, qs):
    user = request.user

    settings = user.settings()
    can_download = settings.can_download

    lastStatus = WaiterStatus.getLastStatus()
    waiterstatus = lastStatus.status if lastStatus else False

    request_params = dict(request.GET)
    offset = int(request_params["start"][0])
    length = int(request_params["length"][0])
    search_str = request_params["search[value]"][0]
    draw = int(request_params["draw"][0])

    sort_columns_map = {
        0: 'filename',
        1: 'datecreated',
    }
    sort_column = int(request_params['order[0][column]'][0])
    sort_dir = request_params['order[0][dir]'][0]
    sort_expr = f'-{sort_columns_map[sort_column]}' if sort_dir == 'desc' else f'{sort_columns_map[sort_column]}'

    initial_qs = qs
    qs = initial_qs.order_by(sort_expr).search(search_str)
    files = qs[offset : offset + length]

    viewed_by_file = UserComment.objects.viewed_by_file(user)
    file_data = [
        file.ajax_row_payload(
            can_download,
            waiterstatus,
            viewed_by_file,
        )
        for file in files
    ]

    payload = {
        "draw": draw,
        "recordsTotal": initial_qs.count(),
        "recordsFiltered": qs.count(),
        "data": file_data,
    }

    return HttpResponse(
        json.dumps(payload), content_type="application/json", status=200
    )


def _ajax_path_rows(request, qs):
    request_params = dict(request.GET)
    offset = int(request_params["start"][0])
    length = int(request_params["length"][0])
    search_str = request_params["search[value]"][0]
    draw = int(request_params["draw"][0])

    sort_columns_map = {
        0: 'localpathstr',
        1: 'lastCreatedFileDate',
    }
    sort_column = int(request_params['order[0][column]'][0])
    sort_dir = request_params['order[0][dir]'][0]
    sort_expr = f'-{sort_columns_map[sort_column]}' if sort_dir == 'desc' else f'{sort_columns_map[sort_column]}'

    initial_qs = qs
    qs = initial_qs.order_by(sort_expr).search(search_str)
    paths = qs[offset : offset + length]

    path_data = [path.ajax_row_payload(request.user) for path in paths]

    payload = {
        "draw": draw,
        "recordsTotal": initial_qs.count(),
        "recordsFiltered": qs.count(),
        "data": path_data,
    }

    return HttpResponse(
        json.dumps(payload), content_type="application/json", status=200
    )


@csrf_exempt
def ajaxmovierows(request):
    qs = File.movies_ordered_by_id()
    return _ajax_file_rows(request, qs)


@csrf_exempt
def ajaxmoviesbygenrerows(request, genre_id):
    genre = get_object_or_404(Genre, pk=genre_id)
    qs = File.movies_by_genre(genre).order_by("-id")
    return _ajax_file_rows(request, qs)


def _get_tv_show_rows_query(genre_id=None):
    paths_qs = (
        Path.objects.filter(is_movie=False)
        .filter(file__hide=False)
        .annotate(num_files=models.Count("file"))
        .filter(num_files__gt=0)
    )

    subquery = models.Subquery(
        Path.objects.filter(localpathstr=models.OuterRef("localpathstr"))
        .order_by("-lastCreatedFileDate")
        .values("pk")[:1]
    )
    paths_qs = Path.objects.filter(
        pk__in=(
            paths_qs.values("localpathstr").annotate(path_pk=subquery).values("path_pk")
        )
    ).order_by("-lastCreatedFileDate")

    if genre_id:
        genre = get_object_or_404(Genre, pk=genre_id)
        paths_qs = paths_qs.filter(_posterfile__genres=genre)
    return paths_qs


@csrf_exempt
def ajaxtvshowssummary(request):
    paths_qs = _get_tv_show_rows_query()
    return _ajax_path_rows(request, paths_qs)


@csrf_exempt
def ajaxtvshowsbygenre(request, genre_id):
    paths_qs = _get_tv_show_rows_query(genre_id)
    return _ajax_path_rows(request, paths_qs)


@csrf_exempt
def ajaxtvshows(request, path_id):
    refpath = get_object_or_404(Path, pk=path_id)
    qs = File.files_by_localpath(refpath).order_by("-display_name")
    return _ajax_file_rows(request, qs)
