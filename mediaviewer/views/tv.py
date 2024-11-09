import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from mediaviewer.models import TV, Comment, Genre, MediaFile
from mediaviewer.utils import humansize, logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext
from mediaviewer.views.ajax import get_tv_show_rows_query


NUMBER_OF_CAROUSEL_FILES = 20
rand = random.SystemRandom()


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshowsummary(request):
    context = {}
    context["active_page"] = "tvshows"
    context["title"] = "TV Shows"
    context["table_data_page"] = "ajaxtvshowssummary"
    context["table_data_filter_id"] = ""

    carousel_files = list(get_tv_show_rows_query()
                          .exclude(_poster__image="")
                          [:NUMBER_OF_CAROUSEL_FILES])
    rand.shuffle(carousel_files)
    context["carousel_files"] = carousel_files

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

    carousel_files = list(get_tv_show_rows_query(genre_id=genre_id)
                          .exclude(_poster__image="")
                          [:NUMBER_OF_CAROUSEL_FILES])
    rand.shuffle(carousel_files)
    context["carousel_files"] = carousel_files

    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/tvsummary.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvshows(request, tv_id):
    user = request.user
    tv = get_object_or_404(TV, pk=tv_id)

    settings = user.settings()
    context = {
        "tv": tv,
        "view": "tvshows",
        "can_download": settings and settings.can_download or False,
        "jump_to_last": (settings and settings.jump_to_last_watched or False),
        "table_data_page": "ajaxtvshows",
    }
    context["table_data_filter_id"] = tv_id
    context["active_page"] = "tvshows"
    context["title"] = tv.name
    context["long_plot"] = len(tv.poster.plot) > 300 if tv.poster.plot else ""
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/tvshows.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def tvdetail(request, mf_id):
    user = request.user
    mf = get_object_or_404(MediaFile, pk=mf_id)

    comment, _ = Comment.objects.get_or_create(
        user=user, media_file=mf, defaults={"viewed": False}
    )

    previous_mf = mf.previous()
    next_mf = mf.next()

    previous_link = reverse('mediaviewer:tvdetail',
                            kwargs=dict(mf_id=previous_mf.pk)
                            ) if previous_mf else None

    next_link = reverse('mediaviewer:tvdetail',
                            kwargs=dict(mf_id=next_mf.pk)
                            ) if next_mf else None

    settings = user.settings()
    context = {
        "mf": mf,
        "display_name": mf.tv.name,
        "episode_name": mf.display_name,
        "poster": mf.poster,
        "viewed": comment.viewed,
        "can_download": settings and settings.can_download or False,
        "file_size": mf.size and humansize(mf.size),
        "obj_type": "media_file",
        "previous_link": previous_link,
        "next_link": next_link,
    }
    context["active_page"] = "tvshows"
    context["title"] = mf.full_name
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/tvdetail.html", context)
