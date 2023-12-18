import json
from itertools import chain

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.message import Message
from mediaviewer.models import Comment, MediaFile, Movie
from mediaviewer.utils import logAccessInfo
from django.shortcuts import get_object_or_404, redirect


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
        return JsonResponse(response, status=400)

    data = dict(request.POST)

    media_files = data.get('media_files', {})
    movies = data.get('movies', {})

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

        comment, was_created = obj.mark_viewed(user, checked, save=False, comment_lookup=comment_lookup)

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

    return JsonResponse(response)


@csrf_exempt
def ajaxsuperviewed(request):
    errmsg = ""
    guid = request.POST.get("guid", '')
    viewed = request.POST["viewed"] == "True" and True or False

    if guid:
        token = DownloadToken.objects.filter(guid=guid).first()
        if token and token.isvalid:
            obj = token.media_file or token.movie
            obj.mark_viewed(token.user, viewed)
        else:
            errmsg = "Token is invalid"
    else:
        errmsg = 'Token is invalid'

    response = {"errmsg": errmsg, "guid": guid, "viewed": viewed}
    return JsonResponse(
        response,
        status=200 if not errmsg else 400,
    )


@logAccessInfo
def ajaxdownloadbutton(request):
    response = {"errmsg": ""}
    mf_id = request.POST.get("mf_id")
    movie_id = request.POST.get("movie_id")

    # Need to raise error
    if mf_id is None and movie_id is None:
        return HttpResponse('Neither mf_id nor movie_id were provided', status=404)
    elif mf_id is not None and movie_id is not None:
        return HttpResponse(
            'Only mf_id or movie_id can be provided. Got both.',
            status=400
        )

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
    dt = DownloadToken.objects.from_media_file(user, mf)

    downloadlink = mf.autoplayDownloadLink(user, dt.guid)
    return redirect(downloadlink)
