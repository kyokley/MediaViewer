from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import url, include
from rest_framework import routers
from django.shortcuts import redirect
from django.conf import settings as conf_settings
from django.urls import reverse_lazy
from mediaviewer.forms import (
    MVSetPasswordForm,
    MVPasswordChangeForm,
    PasswordResetFormWithBCC,
)

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
    PasswordResetCompleteView,
    PasswordChangeView,
    PasswordChangeDoneView,
)

router = routers.DefaultRouter()

urlpatterns = [
    url(r"^$", home.home, name="home"),
    url(r"^files/(?P<file_id>\d+)/$", detail.filesdetail, name="filesdetail"),
    url(r"^files/(?P<file_id>\d+)/comment/$", comment.comment, name="comment"),
    url(r"^files/(?P<file_id>\d+)/results/$", comment.results, name="results"),
    url(r"^tvshows/$", lambda x: redirect("/mediaviewer/tvshows/summary/")),
    url(r"^tvshows/display/(?P<pathid>\d+)/$", files.tvshows, name="tvshows"),
    url(r"^tvshows/(?P<pathid>\d+)/$", files.tvshows, name="tvshows"),
    url(r"^tvshows/summary/$", files.tvshowsummary, name="tvshowsummary"),
    url(
        r"^tvshows/genre/(?P<genre_id>\d+)/$",
        files.tvshows_by_genre,
        name="tvshows_by_genre",
    ),
    url(r"^movies/$", files.movies, name="movies"),
    url(
        r"^movies/genre/(?P<genre_id>\d+)/$",
        files.movies_by_genre,
        name="movies_by_genre",
    ),
    url(r"^downloadlink/(?P<fileid>\d+)/$", detail.downloadlink, name="downloadlink"),
    url(
        r"^autoplaydownloadlink/(?P<fileid>\d+)/$",
        detail.autoplaydownloadlink,
        name="autoplaydownloadlink",
    ),
    url(r"^login/", signin.signin, name="signin"),
    url(r"^logout/", signout.signout, name="signout"),
    url(r"^settings/", settings.settings, name="settings"),
    url(r"^submitsettings/", settings.submitsettings, name="submitsettings"),
    url(
        r"^submitsitesettings/", settings.submitsitesettings, name="submitsitesettings"
    ),
    url(r"^submitnewuser/", settings.submitnewuser, name="submitnewuser"),
    url(
        r"^submitsitewidemessage/",
        messaging.submitsitewidemessage,
        name="submitsitewidemessage",
    ),
    url(r"^requests/", requests.requests, name="requests"),
    url(r"^addrequests/", requests.addrequests, name="addrequests"),
    url(r"^ajaxviewed/", detail.ajaxviewed, name="ajaxviewed"),
    url(r"^ajaxsuperviewed/", detail.ajaxsuperviewed, name="ajaxsuperviewed"),
    url(r"^ajaxvote/", requests.ajaxvote, name="ajaxvote"),
    url(r"^ajaxdone/", requests.ajaxdone, name="ajaxdone"),
    url(r"^ajaxgiveup/", requests.ajaxgiveup, name="ajaxgiveup"),
    url(r"^ajaxdownloadbutton/", detail.ajaxdownloadbutton, name="ajaxdownloadbutton"),
    url(r"^ajaxwaiterstatus/", waiterstatus.ajaxwaiterstatus, name="ajaxwaiterstatus"),
    url(r"^ajaxclosemessage/", messaging.ajaxclosemessage, name="ajaxclosemessage"),
    url(r"^ajaxreport/", files.ajaxreport, name="ajaxreport"),
    url(r"^ajaxrunscraper/", home.ajaxrunscraper, name="ajaxrunscraper"),
    url(
        r"^ajaxvideoprogress/(?P<guid>[0-9A-Za-z]+)/(?P<hashed_filename>.+)/$",
        ajax.ajaxvideoprogress,
        name="ajaxvideoprogress",
    ),
    url(r"^ajaxgenres/(?P<guid>[0-9A-Za-z]+)/$", ajax.ajaxgenres, name="ajaxgenres"),
    url(
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
    url(
        r"^user/reset/done$",
        PasswordResetDoneView.as_view(
            template_name="mediaviewer/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    url(
        r"^user/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        PasswordResetConfirmView.as_view(
            template_name="mediaviewer/password_reset_confirm.html",
            form_class=MVSetPasswordForm,
            success_url=reverse_lazy("mediaviewer:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    url(
        r"^user/create/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        PasswordResetConfirmView.as_view(
            template_name="mediaviewer/password_create_confirm.html",
            form_class=MVSetPasswordForm,
            success_url=reverse_lazy("mediaviewer:password_reset_complete"),
        ),
        name="password_create_confirm",
    ),
    url(
        r"^user/reset/complete$",
        PasswordResetCompleteView.as_view(
            template_name="mediaviewer/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    url(
        r"^user/change_password/$",
        PasswordChangeView.as_view(
            template_name="mediaviewer/change_password.html",
            success_url=reverse_lazy("mediaviewer:change_password_submit"),
            form_class=MVPasswordChangeForm,
        ),
        name="change_password",
    ),
    url(
        r"^user/change_password_submit/$",
        PasswordChangeDoneView.as_view(
            template_name="mediaviewer/change_password_submit.html",
        ),
        name="change_password_submit",
    ),
]

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
    router.register(r"datatransmission", viewset.DataTransmissionViewSet)
    router.register(r"error", viewset.ErrorViewSet)
    router.register(r"message", viewset.MessageViewSet)
    router.register(r"filenamescrapeformat", viewset.FilenameScrapeFormatViewSet)
    router.register(r"posterfilebypath", viewset.PosterViewSetByPath)
    router.register(r"posterfilebyfile", viewset.PosterViewSetByFile)
    router.register(r"usercomment", viewset.UserCommentViewSet)

    urlpatterns += [
        url(r"^api/", include((router.urls, "mediaviewer"), namespace="api")),
        url(r"^api/inferscrapers/", csrf_exempt(viewset.InferScrapersView.as_view())),
    ]
