from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from mediaviewer.api.serializers import DownloadTokenSerializer
from mediaviewer.models import DownloadToken
from mediaviewer.views.b2player_utils import (
    b2_media_path,
    has_b2_source,
    progress_identifier,
)
from mediaviewer.views.views_utils import setSiteWideContext


@login_required(login_url="/mediaviewer/login/")
def b2player(request, guid):
    token = get_object_or_404(DownloadToken, guid=guid)
    if token.user_id != request.user.pk or not token.isvalid:
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

    try:
        source_url = obj.downloadLink(token.guid)
        subtitle_urls = DownloadTokenSerializer().get_subtitle_files(token)
    except (ValueError, TypeError, AttributeError):
        return HttpResponse(status=404)

    if not source_url:
        return HttpResponse(status=404)

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
        "source_url": source_url,
        "subtitle_urls": subtitle_urls,
        "progress_url": progress_url,
        "viewed_url": reverse("mediaviewer:ajaxsuperviewed"),
        "guid": token.guid,
        "binge_mode": user_settings.binge_mode,
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
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response
