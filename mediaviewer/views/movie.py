from django.shortcuts import (
    render,
    get_object_or_404,
)
from mediaviewer.models.usersettings import (
    LOCAL_IP,
    BANGUP_IP,
)
from django.contrib.auth.decorators import login_required
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext
from mediaviewer.models import Genre, Movie, Comment


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
def moviedetail(request, movie_id):
    user = request.user
    movie = get_object_or_404(Movie, pk=movie_id)

    comment, _ = Comment.objects.get_or_create(
        user=user,
        movie=movie,
        defaults={'viewed': False})

    settings = user.settings()
    context = {
        "movie": movie,
        "display_name": movie.name,
        'poster': movie.poster,
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "viewed": comment.viewed,
        "can_download": settings and settings.can_download or False,
    }
    context["active_page"] = "movies"
    context["title"] = (
        movie.name
    )
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/moviedetail.html", context)
