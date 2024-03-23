import json
import re
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import OuterRef, Subquery
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from mediaviewer.models import TV, MediaFile, Movie
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.genre import Genre
from mediaviewer.models.message import Message
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.waiterstatus import WaiterStatus
from mediaviewer.utils import logAccessInfo

REWIND_THRESHOLD = 10  # in minutes
ID_REGEX = re.compile(r"\d+")


@csrf_exempt
def ajaxvideoprogress(request, guid, hashed_filename):
    data = {"offset": 0}
    dt = DownloadToken.objects.get_by_guid(guid)
    if not dt or not dt.user or not dt.isvalid:
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=412
        )

    user = dt.user

    if request.method == "GET":
        vp = VideoProgress.objects.filter(
            user=user, hashed_filename=hashed_filename
        ).first()
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
        vp, _ = VideoProgress.objects.update_or_create(
            user=user,
            hashed_filename=hashed_filename,
            defaults=dict(
                offset=request.POST["offset"],
                movie=dt.movie,
                media_file=dt.media_file,
            ),
        )
        data["offset"] = float(vp.offset)
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=200
        )
    elif request.method == "DELETE":
        VideoProgress.objects.destroy(user, hashed_filename)
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=204
        )
    else:
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=405
        )


@csrf_exempt
def ajaxgenres(request, guid):
    dt = DownloadToken.objects.get_by_guid(guid)
    if not dt or not dt.user or not dt.isvalid:
        return HttpResponse(None, content_type="application/json", status=412)

    if request.method == "GET":
        movie_genres = Genre.objects.get_movie_genres()
        tv_genres = Genre.objects.get_tv_genres()
        data = {
            "movie_genres": [(mg.id, mg.genre) for mg in movie_genres],
            "tv_genres": [(mg.id, mg.genre) for mg in tv_genres],
        }
        return HttpResponse(
            json.dumps(data), content_type="application/json", status=200
        )
    else:
        return HttpResponse(None, content_type="application/json", status=405)


def _ajax_movie_rows(request, qs):
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
        1: "name",
        3: "date_created",
    }
    sort_column = int(request_params.get("order[0][column]", [1])[0])
    sort_dir = request_params.get("order[0][dir]", ["desc"])[0]
    sort_expr = (
        f"-{sort_columns_map[sort_column]}"
        if sort_dir == "desc"
        else f"{sort_columns_map[sort_column]}"
    )

    initial_qs = qs
    qs = initial_qs.order_by(sort_expr).search(search_str)
    files = qs[offset : offset + length]

    file_data = []
    for file in files:
        file_data.append(
            file.ajax_row_payload(
                can_download,
                waiterstatus,
                user,
            )
        )

    payload = {
        "draw": draw,
        "recordsTotal": initial_qs.count(),
        "recordsFiltered": qs.count(),
        "data": file_data,
    }

    return HttpResponse(
        json.dumps(payload), content_type="application/json", status=200
    )


def _ajax_media_file_rows(request, qs):
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
        1: "display_name",
        3: "date_created",
    }
    sort_column = int(request_params.get("order[0][column]", [1])[0])
    sort_dir = request_params.get("order[0][dir]", ["desc"])[0]
    sort_expr = (
        f"-{sort_columns_map[sort_column]}"
        if sort_dir == "desc"
        else f"{sort_columns_map[sort_column]}"
    )

    initial_qs = qs
    qs = initial_qs.order_by(sort_expr).search(search_str)

    mfs = qs[offset : offset + length]

    mf_data = []
    for mf in mfs:
        mf_data.append(mf.ajax_row_payload(can_download, waiterstatus, user))

    payload = {
        "draw": draw,
        "recordsTotal": initial_qs.count(),
        "recordsFiltered": qs.count(),
        "data": mf_data,
    }

    return HttpResponse(
        json.dumps(payload), content_type="application/json", status=200
    )


def _ajax_tv_rows(request, qs):
    request_params = dict(request.GET)
    offset = int(request_params["start"][0])
    length = int(request_params["length"][0])
    search_str = request_params["search[value]"][0]
    draw = int(request_params["draw"][0])

    sort_columns_map = {
        0: "name",
        1: "max_date_created",
    }
    sort_column = int(request_params.get("order[0][column]", [1])[0])
    sort_dir = request_params.get("order[0][dir]", ["desc"])[0]
    sort_expr = (
        f"-{sort_columns_map[sort_column]}"
        if sort_dir == "desc"
        else f"{sort_columns_map[sort_column]}"
    )

    initial_qs = qs
    qs = initial_qs.order_by(sort_expr).search(search_str)
    tvs = qs[offset : offset + length]

    tv_data = [tv.ajax_row_payload(request.user) for tv in tvs]

    payload = {
        "draw": draw,
        "recordsTotal": initial_qs.count(),
        "recordsFiltered": qs.count(),
        "data": tv_data,
    }

    return HttpResponse(
        json.dumps(payload), content_type="application/json", status=200
    )


@csrf_exempt
def ajaxmovierows(request):
    qs = Movie.objects.order_by("-id")
    return _ajax_movie_rows(request, qs)


@csrf_exempt
def ajaxmoviesbygenrerows(request, genre_id):
    genre = get_object_or_404(Genre, pk=genre_id)
    qs = Movie.objects.filter(_poster__genres=genre).order_by("-id")
    return _ajax_movie_rows(request, qs)


def _get_tv_show_rows_query(genre_id=None):
    tv_qs = TV.objects.annotate(
        max_date_created=Subquery(
            MediaFile.objects.filter(media_path__tv=OuterRef("pk"))
            .order_by("-date_created")
            .values("date_created")[:1]
        )
    ).order_by("-max_date_created")

    if genre_id:
        genre = get_object_or_404(Genre, pk=genre_id)
        tv_qs = tv_qs.filter(_poster__genres=genre)
    return tv_qs


@csrf_exempt
def ajaxtvshowssummary(request):
    paths_qs = _get_tv_show_rows_query()
    return _ajax_tv_rows(request, paths_qs)


@csrf_exempt
def ajaxtvshowsbygenre(request, genre_id):
    paths_qs = _get_tv_show_rows_query(genre_id)
    return _ajax_tv_rows(request, paths_qs)


@csrf_exempt
def ajaxtvshows(request, tv_id):
    ref_tv = get_object_or_404(TV, pk=tv_id)

    qs = MediaFile.objects.filter(media_path__tv=ref_tv).order_by("display_name")

    return _ajax_media_file_rows(request, qs)


@logAccessInfo
def ajaxreport(request):
    response = {"errmsg": ""}
    try:
        createdBy = request.user
        mf_id = request.POST.get("mf_id")
        movie_id = request.POST.get("movie_id")

        mf_id = int(mf_id) if mf_id is not None else None
        movie_id = int(movie_id) if movie_id is not None else None

        if mf_id is not None:
            obj = get_object_or_404(MediaFile, pk=mf_id)
        elif movie_id is not None:
            obj = get_object_or_404(Movie, pk=movie_id)
        else:
            return HttpResponse(
                "Either mf_id or movie_id must be provided.", status=400
            )

        response["reportid"] = obj.pk
        users = User.objects.filter(is_staff=True)

        for user in users:
            Message.createNewMessage(
                user,
                f"{obj.name} has been reported by {createdBy.username}",
                level=messages.WARNING,
            )
    except Http404:
        raise
    except Exception as e:
        if settings.DEBUG:
            response["errmsg"] = str(e)
        else:
            response["errmsg"] = "An error has occurred"
    return JsonResponse(response)
