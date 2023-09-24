from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from mediaviewer.models.file import File
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.views.views_utils import setSiteWideContext
from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)
from mediaviewer.models.message import Message
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models import Poster
from mediaviewer.utils import logAccessInfo, humansize
from django.shortcuts import render, get_object_or_404, redirect
import json


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def filesdetail(request, file_id):
    user = request.user
    file = File.objects.get(pk=file_id)
    skip = file.skip
    finished = file.finished
    usercomment = file.usercomment(user)
    if usercomment:
        viewed = usercomment.viewed
        comment = usercomment.comment or ""
        setattr(file, "usercomment", usercomment)
    else:
        viewed = False
        comment = ""

    poster = Poster.objects.get(media_file__filename=file.filename)

    settings = user.settings()
    context = {
        "file": file,
        "displayName": file.displayName(),
        'poster': poster,
        "comment": comment,
        "skip": skip,
        "finished": finished,
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "viewed": viewed,
        "can_download": settings and settings.can_download or False,
        "file_size": file.size and humansize(file.size),
    }
    context["active_page"] = "movies" if file.isMovie() else "tvshows"
    context["title"] = (
        file.isMovie() and file.rawSearchString() or file.path.displayName()
    )
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/filesdetail.html", context)


@csrf_exempt
@logAccessInfo
def ajaxviewed(request):
    errmsg = None
    user = request.user
    response = {"errmsg": ""}
    if not user.is_authenticated:
        errmsg = "User not authenticated. Refresh and try again."

    if errmsg:
        response["errmsg"] = errmsg
        return HttpResponse(json.dumps(response), content_type="application/javascript")

    data = dict(request.POST)
    data.pop("csrfmiddlewaretoken", None)

    updated = []
    updated_comments = []
    created_comments = []

    qs = File.objects.filter(pk__in=data.keys())
    uc_qs = UserComment.objects.filter(user=user).filter(file__in=qs)
    uc_lookup = {uc.file: uc for uc in uc_qs}

    for file in qs:
        checked = data[str(file.pk)]
        viewed = checked[0].lower() == "true" and True or False
        comment, was_created = file.markFileViewed(
            user, viewed, save=False, uc_lookup=uc_lookup
        )
        if was_created:
            created_comments.append(comment)
        else:
            updated_comments.append(comment)

        updated.append(str(file.pk))

    if created_comments:
        UserComment.objects.bulk_create(created_comments)

    if updated_comments:
        UserComment.objects.bulk_update(updated_comments, ["viewed", "dateedited"])

    if created_comments or updated_comments:
        Message.clearLastWatchedMessage(user)

    response["data"] = data

    return HttpResponse(json.dumps(response), content_type="application/javascript")


@csrf_exempt
def ajaxsuperviewed(request):
    errmsg = ""
    guid = request.POST["guid"]
    viewed = request.POST["viewed"] == "True" and True or False

    token = DownloadToken.objects.filter(guid=guid).first()
    if token and token.isvalid:
        token.file.markFileViewed(token.user, viewed)
    else:
        errmsg = "Token is invalid"

    response = {"errmsg": errmsg, "guid": guid, "viewed": viewed}
    response = json.dumps(response)
    return HttpResponse(
        response, status=200 if not errmsg else 400, content_type="application/json"
    )


@logAccessInfo
def ajaxdownloadbutton(request):
    response = {"errmsg": ""}
    fileid = int(request.POST["fileid"])
    file = get_object_or_404(File, pk=fileid)
    user = request.user

    if not user.is_authenticated:
        response = {"errmsg": "User not authenticated. Refresh and try again."}
    elif file and user:
        dt = DownloadToken.new(user, file)

        downloadlink = file.downloadLink(user, dt.guid)
        response = {
            "guid": dt.guid,
            "isMovie": dt.ismovie,
            "downloadLink": downloadlink,
            "errmsg": "",
        }
    else:
        response = {"errmsg": "An error has occurred"}

    return HttpResponse(json.dumps(response), content_type="application/javascript")


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def downloadlink(request, fileid):
    user = request.user
    file = get_object_or_404(File, pk=fileid)
    dt = DownloadToken.new(user, file)

    downloadlink = file.downloadLink(user, dt.guid)
    return redirect(downloadlink)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def autoplaydownloadlink(request, fileid):
    user = request.user
    file = get_object_or_404(File, pk=fileid)
    dt = DownloadToken.new(user, file)

    downloadlink = file.autoplayDownloadLink(user, dt.guid)
    return redirect(downloadlink)
