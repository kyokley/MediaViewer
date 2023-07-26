from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import include
from django.urls import re_path
from rest_framework import routers
from django.shortcuts import redirect
from django.conf import settings as conf_settings
from django.urls import reverse_lazy
from mediaviewer.forms import PasswordResetFormWithBCC

from mediaviewer.views import (
    home,
    files,
    detail,
    comment,
    signin,
    signout,
    settings,
    messaging,
    requests,
    waiterstatus,
    ajax,
)
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
)

router = routers.DefaultRouter()

urlpatterns = [
    re_path(r"^$", home.home, name="home"),
    re_path(r"^files/(?P<file_id>\d+)/$", detail.filesdetail, name="filesdetail"),
    re_path(r"^files/(?P<file_id>\d+)/comment/$", comment.comment, name="comment"),
    re_path(r"^files/(?P<file_id>\d+)/results/$", comment.results, name="results"),
    re_path(r"^tvshows/$", lambda x: redirect("/mediaviewer/tvshows/summary/")),
    re_path(r"^tvshows/display/(?P<pathid>\d+)/$", files.tvshows, name="tvshows"),
    re_path(r"^tvshows/(?P<pathid>\d+)/$", files.tvshows, name="tvshows"),
    re_path(r"^tvshows/summary/$", files.tvshowsummary, name="tvshowsummary"),
    re_path(
        r"^tvshows/genre/(?P<genre_id>\d+)/$",
        files.tvshows_by_genre,
        name="tvshows_by_genre",
    ),
    re_path(r"^movies/$", files.movies, name="movies"),
    re_path(
        r"^movies/genre/(?P<genre_id>\d+)/$",
        files.movies_by_genre,
        name="movies_by_genre",
    ),
    re_path(
        r"^downloadlink/(?P<fileid>\d+)/$", detail.downloadlink, name="downloadlink"
    ),
    re_path(
        r"^autoplaydownloadlink/(?P<fileid>\d+)/$",
        detail.autoplaydownloadlink,
        name="autoplaydownloadlink",
    ),
    re_path(r"^settings/", settings.settings, name="settings"),
    re_path(r"^submitsettings/", settings.submitsettings, name="submitsettings"),
    re_path(
        r"^submitsitesettings/", settings.submitsitesettings, name="submitsitesettings"
    ),
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
    re_path(r"^ajaxreport/", files.ajaxreport, name="ajaxreport"),
    re_path(r"^ajaxrunscraper/", home.ajaxrunscraper, name="ajaxrunscraper"),
    re_path(
        r"^ajaxvideoprogress/(?P<guid>[0-9A-Za-z]+)/(?P<hashed_filename>.+)/$",
        ajax.ajaxvideoprogress,
        name="ajaxvideoprogress",
    ),
    re_path(
        r"^ajaxgenres/(?P<guid>[0-9A-Za-z]+)/$", ajax.ajaxgenres, name="ajaxgenres"
    ),
    re_path(r"^ajax/ajaxmovierows/$", ajax.ajaxmovierows, name="ajaxmovierows"),
    re_path(r"^ajax/ajaxfilesrows/$", ajax.ajaxfilesrows, name="ajaxfilesrows"),
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
        r"^ajax/ajaxtvshows/(?P<path_id>[0-9]+)/$",
        ajax.ajaxtvshows,
        name="ajaxtvshows",
    ),
    re_path(
        r"^user/reset/$",
        PasswordResetView.as_view(
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
        PasswordResetDoneView.as_view(
            template_name="mediaviewer/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    re_path(
        r"^user/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        PasswordResetConfirmView.as_view(
            template_name="mediaviewer/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    re_path(
        r"^user/create/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        PasswordResetConfirmView.as_view(
            template_name="mediaviewer/password_reset_confirm.html",
        ),
        name="password_create_confirm",
    ),
]

urlpatterns.extend(
    [
        re_path(r"^login/", signin.signin, name="signin"),
        re_path(
            rf"^bypass-passkey/(?P<uidb64>[0-9A-Za-z]+)-{PasswordResetConfirmView.reset_url_token}/$",
            signin.bypass_passkey,
            name="bypass-passkey",
        ),
        re_path(
            rf"^create-token/(?P<uidb64>[0-9A-Za-z]+)-{PasswordResetConfirmView.reset_url_token}/$",
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
    from mediaviewer.api import viewset, path_viewset, file_viewset

    router.register(
        r"downloadtoken", viewset.DownloadTokenViewSet, basename="downloadtoken"
    )
    router.register(
        r"unstreamablefile",
        file_viewset.UnstreamableFileViewSet,
        basename="unstreamablefile",
    )
    router.register(r"movie", file_viewset.MovieFileViewSet, basename="movie")
    router.register(r"tv", file_viewset.TvFileViewSet, basename="tv")
    router.register(r"tvpath", path_viewset.TvPathViewSet, basename="tvpath")
    router.register(r"moviepath", path_viewset.MoviePathViewSet, basename="moviepath")
    router.register(
        r"distinct-tv", path_viewset.DistinctTvPathViewSet, basename="distinct-tv"
    )
    router.register(r"error", viewset.ErrorViewSet)
    router.register(r"message", viewset.MessageViewSet)
    router.register(r"filenamescrapeformat", viewset.FilenameScrapeFormatViewSet)
    router.register(r"posterfilebypath", viewset.PosterViewSetByPath)
    router.register(r"posterfilebyfile", viewset.PosterViewSetByFile)
    router.register(r"usercomment", viewset.UserCommentViewSet)

    urlpatterns += [
        re_path(r"^api/", include((router.urls, "mediaviewer"), namespace="api")),
        re_path(
            r"^api/inferscrapers/", csrf_exempt(viewset.InferScrapersView.as_view())
        ),
    ]
