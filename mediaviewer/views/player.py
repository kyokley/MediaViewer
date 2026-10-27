from functools import wraps

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from mediaviewer.api.serializers import DownloadTokenSerializer
from mediaviewer.b2 import B2Error
from mediaviewer.models import DownloadToken
from mediaviewer.views.b2player_utils import (
    b2_media_path,
    has_b2_source,
    progress_identifier,
)
from mediaviewer.views.views_utils import setSiteWideContext


def _b2_player_access(request, guid):
    token = DownloadToken.objects.filter(guid=guid).first()
    if not token or token.user_id != request.user.pk or not token.isvalid:
        return HttpResponse(status=404)

    user_settings = request.user.settings()
    if not user_settings or not user_settings.can_download:
        return HttpResponseForbidden()

    obj = token.ref_obj
    if not obj:
        return HttpResponse(status=404)
    media_path = b2_media_path(obj)
    if not media_path or not has_b2_source(obj, media_path):
        return HttpResponse(status=404)
    return token, obj, media_path, user_settings


def _sensitive_response(response):
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


def _sensitive_view(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        return _sensitive_response(view(*args, **kwargs))

    return wrapped


def notfound(request):
    context = {"title": "Page not found"}
    setSiteWideContext(context, request)
    response = render(request, "mediaviewer/404.html", context, status=404)
    return _sensitive_response(response)


@login_required(login_url="/mediaviewer/login/")
def b2player(request, guid):
    access = _b2_player_access(request, guid)
    if isinstance(access, HttpResponse):
        if access.status_code == 404:
            return _sensitive_response(redirect(reverse("mediaviewer:notfound")))
        return access
    token, obj, media_path, user_settings = access

    linked_movie = token.movie or (token.media_file.movie if token.media_file else None)
    is_movie = linked_movie is not None
    if is_movie:
        details_url = reverse("mediaviewer:moviedetail", args=(linked_movie.pk,))
        previous_url = next_url = None
    else:
        details_url = reverse("mediaviewer:tvdetail", args=(token.media_file_id,))
        previous_obj = obj.previous()
        next_obj = obj.next()
        previous_url = (
            reverse("mediaviewer:autoplaydownloadlink", args=(previous_obj.pk,))
            if previous_obj
            else None
        )
        next_url = (
            reverse("mediaviewer:autoplaydownloadlink", args=(next_obj.pk,))
            if next_obj
            else None
        )

    progress_url = reverse(
        "mediaviewer:ajaxvideoprogress",
        kwargs={
            "guid": token.guid,
            "hashed_filename": progress_identifier(token, obj, media_path),
        },
    )
    player_config = {
        "media_url": reverse("mediaviewer:b2playermedia", args=(token.guid,)),
        "progress_url": progress_url,
        "viewed_url": reverse("mediaviewer:ajaxsuperviewed"),
        "guid": token.guid,
        "binge_mode": user_settings.binge_mode,
        "captions_enabled": user_settings.captions_enabled,
        "captions_url": reverse("mediaviewer:b2playercaptions", args=(token.guid,)),
        "next_url": next_url,
    }
    context = {
        "display_name": token.displayname,
        "details_url": details_url,
        "is_movie": is_movie,
        "previous_url": previous_url,
        "next_url": next_url,
        "poster_url": token.og_image or None,
        "player_config": player_config,
    }
    setSiteWideContext(context, request)
    response = render(request, "mediaviewer/b2player.html", context)
    return _sensitive_response(response)


@_sensitive_view
@login_required(login_url="/mediaviewer/login/")
@require_POST
@csrf_protect
def b2playercaptions(request, guid):
    access = _b2_player_access(request, guid)
    if isinstance(access, HttpResponse):
        return access
    _token, _obj, _media_path, user_settings = access

    captions_enabled = request.POST.get("captions_enabled")
    if captions_enabled not in ("true", "false"):
        return HttpResponse(status=400)

    user_settings.captions_enabled = captions_enabled == "true"
    user_settings.dateedited = timezone.now()
    user_settings.save(update_fields=("captions_enabled", "dateedited"))
    return HttpResponse(status=204)


@_sensitive_view
@require_GET
@login_required(login_url="/mediaviewer/login/")
def b2playermedia(request, guid):
    access = _b2_player_access(request, guid)
    if isinstance(access, HttpResponse):
        return access
    token, obj, _media_path, _user_settings = access

    try:
        source_url = obj.downloadLink(token.guid)
        subtitle_urls = DownloadTokenSerializer().get_subtitle_files(token)
    except (ValueError, TypeError, AttributeError):
        return HttpResponse(status=404)
    except (requests.RequestException, B2Error):
        return HttpResponse("Media URL generation failed", status=502)

    if not source_url:
        return HttpResponse(status=404)
    return JsonResponse({"source_url": source_url, "subtitle_urls": subtitle_urls})
