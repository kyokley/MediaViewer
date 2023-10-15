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
from mediaviewer.models import TV, MediaFile, Comment, Genre


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshowsummary(request):
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
    context = {}
    context["active_page"] = "tvshows"
    context["title"] = "TV Shows: {}".format(ref_genre.genre)
    context["table_data_page"] = "ajaxtvshowsbygenre"
    context["table_data_filter_id"] = genre_id
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/tvsummary.html", context)


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
    mf = get_object_or_404(MediaFile, pk=mf_id)

    comment, _ = Comment.objects.get_or_create(
        user=user,
        media_file=mf,
        defaults={'viewed': False})

    settings = user.settings()
    context = {
        "mf": mf,
        "display_name": mf.tv.name,
        'episode_name': mf.display_name,
        'poster': mf.poster,
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "viewed": comment.viewed,
        "can_download": settings and settings.can_download or False,
        "file_size": mf.size and humansize(mf.size),
        'obj_type': 'media_file',
    }
    context["active_page"] = "tvshows"
    context["title"] = (
        mf.full_name
    )
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/tvdetail.html", context)
