from django.http import HttpResponse, Http404
from django.shortcuts import (
    render,
    get_object_or_404,
)

from mediaviewer.models.file import File
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth.decorators import login_required
from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)
from mediaviewer.models.genre import Genre
from mediaviewer.models.path import Path
from mediaviewer.models.usercomment import UserComment
from django.contrib.auth.models import User
from mediaviewer.models.message import Message
from django.contrib import messages
from django.conf import settings
from mediaviewer.utils import logAccessInfo

import json
import re

ID_REGEX = re.compile(r"\d+")


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def files(request, items):
    user = request.user
    items = int(items)
    if items:
        files = File.objects.order_by("-id")[:items]
    else:
        files = File.objects.order_by("-id")
    files = files.select_related("path")

    settings = user.settings()
    context = {
        "items": items,
        "view": "files",
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "can_download": (settings and settings.can_download or False),
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "ajaxfilesrows",
    }
    context["active_page"] = "files"
    context["title"] = "Files"
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/files.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def movies(request):
    user = request.user

    settings = user.settings()
    context = {
        "view": "movies",
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "can_download": settings and settings.can_download or False,
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "ajaxmovierows",
    }
    context["active_page"] = "movies"
    context["title"] = "Movies"
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/files.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def movies_by_genre(request, genre_id):
    user = request.user
    genre = get_object_or_404(Genre, pk=genre_id)

    settings = user.settings()
    context = {
        "view": "movies",
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "can_download": settings and settings.can_download or False,
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "ajaxmoviesbygenrerows",
        "table_data_filter_id": genre.id,
    }
    context["active_page"] = "movies"
    context["title"] = "Movies: {}".format(genre.genre)
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/files.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshowsummary(request):
    # pathDict = Path.distinctShowFolders()
    # pathSet = [path for name, path in pathDict.items()]

    # context = {"pathSet": pathSet}
    context = {}
    context["active_page"] = "tvshows"
    context["title"] = "TV Shows"
    context["table_data_page"] = "ajaxtvshowssummary"
    context["table_data_filter_id"] = ""
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/tvsummary.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshows_by_genre(request, genre_id):
    ref_genre = get_object_or_404(Genre, pk=genre_id)
    # pathDict = Path.distinctShowFoldersByGenre(ref_genre)
    # pathSet = [path for name, path in pathDict.items()]

    # context = {"pathSet": pathSet}
    context = {}
    context["active_page"] = "tvshows"
    context["title"] = "TV Shows: {}".format(ref_genre.genre)
    context["table_data_page"] = "ajaxtvshowsbygenre"
    context["table_data_filter_id"] = ""
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/tvsummary.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshows(request, pathid):
    user = request.user
    refpath = get_object_or_404(Path, pk=pathid)
    files = File.files_by_localpath(refpath).select_related("path")

    viewed_by_file = UserComment.objects.viewed_by_file(user)
    file_data = [file.display_payload() for file in files]
    for file in file_data:
        file["viewed"] = viewed_by_file.get(file["id"], False)

    settings = user.settings()
    context = {
        "files": file_data,
        "path": refpath,
        "view": "tvshows",
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "can_download": settings and settings.can_download or False,
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "tvshows",
    }
    context["active_page"] = "tvshows"
    context["title"] = refpath.displayName()
    context["long_plot"] = (
        len(refpath.posterfile.plot) > 300 if refpath.posterfile.plot else ""
    )
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/files.html", context)


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
