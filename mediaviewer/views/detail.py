import json
from itertools import chain

from django.db import transaction
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
from mediaviewer.models import Poster, Comment, MediaFile, Movie
from mediaviewer.utils import logAccessInfo, humansize
from django.shortcuts import render, get_object_or_404, redirect


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
@transaction.atomic
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

    media_files = data.pop('media_files', [])
    movies = data.pop('movies', [])

    updated_comments = []
    created_comments = []

    mf_qs = MediaFile.objects.filter(pk__in=media_files.keys())
    movie_qs = Movie.objects.filter(pk__in=movies.keys())

    mf_comment_qs = Comment.objects.filter(user=user).filter(media_file__in=mf_qs)
    movie_comment_qs = Comment.objects.filter(user=user).filter(movie__in=movie_qs)

    comment_lookup = {comment.media_file: comment for comment in mf_comment_qs}
    comment_lookup.update({comment.movie: comment for comment in movie_comment_qs})

    for obj in chain(mf_qs, movie_qs):
        if isinstance(obj, MediaFile):
            checked = media_files[str(obj.pk)]
        else:
            checked = movies[str(obj.pk)]

        viewed = checked[0].lower() == "true" and True or False
        comment, was_created = obj.mark_viewed(user, viewed, save=False, comment_lookup=comment_lookup)

        if was_created:
            created_comments.append(comment)
        else:
            updated_comments.append(comment)


    if created_comments:
        Comment.objects.bulk_create(created_comments)

    if updated_comments:
        Comment.objects.bulk_update(updated_comments, ["viewed"])

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
        obj = token.media_file or token.movie
        obj.mark_viewed(token.user, viewed)
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
    mf_id = request.POST.get("mf_id")
    movie_id = request.POST.get("movie_id")

    # Need to raise error
    if mf_id is None and movie_id is None:
        pass
    elif mf_id is not None and movie_id is not None:
        pass

    if mf_id is not None:
        obj = get_object_or_404(MediaFile, pk=mf_id)
    else:
        obj = get_object_or_404(Movie, pk=movie_id)
    user = request.user

    if not user.is_authenticated:
        response = {"errmsg": "User not authenticated. Refresh and try again."}
    elif obj and user:
        if isinstance(obj, MediaFile):
            dt = DownloadToken.objects.from_media_file(user, obj)
        else:
            dt = DownloadToken.objects.from_movie(user, obj)

        downloadlink = obj.downloadLink(user, dt.guid)
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
def autoplaydownloadlink(request, mf_id):
    user = request.user
    mf = get_object_or_404(MediaFile, pk=mf_id)
    dt = DownloadToken.new(user, mf)

    downloadlink = mf.autoplayDownloadLink(user, dt.guid)
    return redirect(downloadlink)
