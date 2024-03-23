from django.conf import settings as conf_settings
from django.conf.urls import include
from django.shortcuts import redirect
from django.urls import re_path, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from mediaviewer.forms import PasswordResetFormWithBCC
from mediaviewer.views import (ajax, detail, home, messaging, movie, requests,
                               settings, signin, signout, tv, waiterstatus)

router = routers.DefaultRouter()

urlpatterns = [
    re_path(r"^$", home.home, name="home"),
    re_path(r"^tvdetail/(?P<mf_id>\d+)/$", tv.tvdetail, name="tvdetail"),
    re_path(r"^tvshows/$", lambda x: redirect("/mediaviewer/tvshows/summary/")),
    re_path(r"^tvshows/(?P<tv_id>\d+)/$", tv.tvshows, name="tvshows"),
    re_path(r"^tvshows/summary/$", tv.tvshowsummary, name="tvshowsummary"),
    re_path(
        r"^tvshows/genre/(?P<genre_id>\d+)/$",
        tv.tvshows_by_genre,
        name="tvshows_by_genre",
    ),
    re_path(r"^movies/$", movie.movies, name="movies"),
    re_path(
        r"^movies/genre/(?P<genre_id>\d+)/$",
        movie.movies_by_genre,
        name="movies_by_genre",
    ),
    re_path(r"^moviedetail/(?P<movie_id>\d+)/$", movie.moviedetail, name="moviedetail"),
    re_path(
        r"^autoplaydownloadlink/(?P<mf_id>\d+)/$",
        detail.autoplaydownloadlink,
        name="autoplaydownloadlink",
    ),
    re_path(r"^settings/", settings.settings, name="settings"),
    re_path(r"^submitsettings/", settings.submitsettings, name="submitsettings"),
    re_path(r"^submitnewuser/", settings.submitnewuser, name="submitnewuser"),
    re_path(
        r"^submitsitewidemessage/",
        messaging.submitsitewidemessage,
        name="submitsitewidemessage",
    ),
    re_path(r"^requests/", requests.requests, name="requests"),
    re_path(r"^addrequests/", requests.addrequests, name="addrequests"),
    re_path(r"^ajaxviewed/", detail.ajaxviewed, name="ajaxviewed"),
    re_path(r"^ajaxsuperviewed/", detail.ajaxsuperviewed, name="ajaxsuperviewed"),
    re_path(r"^ajaxvote/", requests.ajaxvote, name="ajaxvote"),
    re_path(r"^ajaxdone/", requests.ajaxdone, name="ajaxdone"),
    re_path(r"^ajaxgiveup/", requests.ajaxgiveup, name="ajaxgiveup"),
    re_path(
        r"^ajaxdownloadbutton/", detail.ajaxdownloadbutton, name="ajaxdownloadbutton"
    ),
    re_path(
        r"^ajaxwaiterstatus/", waiterstatus.ajaxwaiterstatus, name="ajaxwaiterstatus"
    ),
    re_path(r"^ajaxclosemessage/", messaging.ajaxclosemessage, name="ajaxclosemessage"),
    re_path(r"^ajaxreport/", ajax.ajaxreport, name="ajaxreport"),
    re_path(
        r"^ajaxvideoprogress/(?P<guid>[0-9A-Za-z]+)/(?P<hashed_filename>.+)/$",
        ajax.ajaxvideoprogress,
        name="ajaxvideoprogress",
    ),
    re_path(
        r"^ajaxgenres/(?P<guid>[0-9A-Za-z]+)/$", ajax.ajaxgenres, name="ajaxgenres"
    ),
    re_path(r"^ajax/ajaxmovierows/$", ajax.ajaxmovierows, name="ajaxmovierows"),
    re_path(
        r"^ajax/ajaxmoviesbygenrerows/(?P<genre_id>[0-9]+)/$",
        ajax.ajaxmoviesbygenrerows,
        name="ajaxmoviesbygenrerows",
    ),
    re_path(
        r"^ajax/ajaxtvshowssummary/$",
        ajax.ajaxtvshowssummary,
        name="ajaxtvshowssummary",
    ),
    re_path(
        r"^ajax/ajaxtvshowsbygenre/(?P<genre_id>[0-9]+)/$",
        ajax.ajaxtvshowsbygenre,
        name="ajaxtvshowsbygenre",
    ),
    re_path(
        r"^ajax/ajaxtvshows/(?P<tv_id>[0-9]+)/$",
        ajax.ajaxtvshows,
        name="ajaxtvshows",
    ),
    re_path(
        r"^user/reset/$",
        signin.PasswordResetView.as_view(
            template_name="mediaviewer/password_reset_form.html",
            email_template_name="mediaviewer/password_reset_email.html",
            subject_template_name="mediaviewer/password_reset_subject.txt",
            success_url=reverse_lazy("mediaviewer:password_reset_done"),
            form_class=PasswordResetFormWithBCC,
        ),
        name="password_reset",
    ),
    re_path(
        r"^user/reset/done$",
        signin.PasswordResetDoneView.as_view(
            template_name="mediaviewer/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    re_path(
        r"^user/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        signin.PasswordResetConfirmView.as_view(
            template_name="mediaviewer/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    re_path(
        r"^user/create/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        signin.PasswordResetConfirmView.as_view(
            template_name="mediaviewer/password_reset_confirm.html",
        ),
        name="password_create_confirm",
    ),
]

urlpatterns.extend(
    [
        re_path(r"^login/", signin.signin, name="signin"),
        re_path(r"^legacy-login/", signin.legacy_signin, name="legacy-signin"),
        re_path(
            rf"^bypass-passkey/(?P<uidb64>[0-9A-Za-z]+)-{signin.PasswordResetConfirmView.reset_url_token}/$",
            signin.bypass_passkey,
            name="bypass-passkey",
        ),
        re_path(
            rf"^create-token/(?P<uidb64>[0-9A-Za-z]+)-{signin.PasswordResetConfirmView.reset_url_token}/$",
            signin.create_token,
            name="create-token",
        ),
        re_path(
            r"^create-token-complete/",
            signin.create_token_complete,
            name="create-token-complete",
        ),
        re_path(
            r"^create-token-failed/",
            signin.create_token_failed,
            name="create-token-failed",
        ),
        re_path(r"^verify-token/", signin.verify_token, name="verify-token"),
        re_path(r"^logout/", signout.signout, name="signout"),
    ]
)

if not conf_settings.IS_SYNCING:
    from mediaviewer.api import (media_file_viewset, media_path_viewset,
                                 movie_viewset, tv_viewset, viewset)

    router.register(
        r"downloadtoken", viewset.DownloadTokenViewSet, basename="downloadtoken"
    )
    router.register(r"movie", movie_viewset.MovieViewSet, basename="movie")
    router.register(r"tv", tv_viewset.TVViewSet, basename="tv")
    router.register(
        r"tvmediapath", media_path_viewset.TVMediaPathViewSet, basename="tvmediapath"
    )
    router.register(
        r"moviemediapath",
        media_path_viewset.MovieMediaPathViewSet,
        basename="moviemediapath",
    )
    router.register(
        r"mediafile", media_file_viewset.MediaFileViewSet, basename="mediafile"
    )
    router.register(r"message", viewset.MessageViewSet)
    router.register(r"filenamescrapeformat", viewset.FilenameScrapeFormatViewSet)
    router.register(r"comment", viewset.CommentViewSet)

    urlpatterns += [
        re_path(r"^api/", include((router.urls, "mediaviewer"), namespace="api")),
        re_path(
            r"^api/inferscrapers/", csrf_exempt(viewset.InferScrapersView.as_view())
        ),
    ]
