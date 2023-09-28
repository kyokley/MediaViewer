from mediaviewer.utils import logAccessInfo, humansize
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    render,
    get_object_or_404,
)
from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)
from mediaviewer.views.views_utils import setSiteWideContext
from mediaviewer.models import TV, MediaFile, Comment


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshows(request, tv_id):
    user = request.user
    tv = get_object_or_404(TV, pk=tv_id)

    settings = user.settings()
    context = {
        'tv': tv,
        "view": "tvshows",
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "can_download": settings and settings.can_download or False,
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "ajaxtvshows",
    }
    context["table_data_filter_id"] = tv_id
    context["active_page"] = "tvshows"
    context["title"] = tv.name
    context["long_plot"] = (
        len(tv.poster.plot) > 300 if tv.poster.plot else ""
    )
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/tvshows.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvdetail(request, mf_id):
    user = request.user
    file = MediaFile.objects.get(pk=mf_id)

    comment, _ = Comment.objects.get_or_create(
        user=user,
        media_file=file,
        defaults={'viewed': False})

    settings = user.settings()
    context = {
        "file": file,
        "display_name": file.tv.name,
        'episode_name': file.display_name,
        'poster': file.poster,
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "viewed": comment.viewed,
        "can_download": settings and settings.can_download or False,
        "file_size": file.size and humansize(file.size),
    }
    context["active_page"] = "tvshows"
    context["title"] = (
        file.full_name
    )
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/tvdetail.html", context)
