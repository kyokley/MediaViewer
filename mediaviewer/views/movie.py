import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from mediaviewer.models import Comment, Genre, Movie
from mediaviewer.models.usersettings import BANGUP_IP, LOCAL_IP
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


NUMBER_OF_CAROUSEL_FILES = 10
rand = random.SystemRandom()


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
    carousel_files = list(
            Movie.objects
            .exclude(_poster__image="")
            .filter(hide=False)
            .order_by('-_poster__release_date')[:NUMBER_OF_CAROUSEL_FILES]
            )
    rand.shuffle(carousel_files)
    context["carousel_files"] = carousel_files
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/movies.html", context)


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

    carousel_files = list(
            Movie.objects
            .exclude(_poster__image="")
            .filter(hide=False)
            .filter(_poster__genres=genre)
            .order_by('-_poster__release_date')[:NUMBER_OF_CAROUSEL_FILES]
            )
    rand.shuffle(carousel_files)
    context["carousel_files"] = carousel_files
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, "mediaviewer/movies.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def moviedetail(request, movie_id):
    user = request.user
    movie = get_object_or_404(Movie, pk=movie_id)

    comment, _ = Comment.objects.get_or_create(
        user=user, movie=movie, defaults={"viewed": False}
    )

    settings = user.settings()
    context = {
        "movie": movie,
        "display_name": movie.name,
        "poster": movie.poster,
        "LOCAL_IP": LOCAL_IP,
        "BANGUP_IP": BANGUP_IP,
        "viewed": comment.viewed,
        "can_download": settings and settings.can_download or False,
        "obj_type": "movie",
    }
    context["active_page"] = "movies"
    context["title"] = movie.name
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/moviedetail.html", context)
