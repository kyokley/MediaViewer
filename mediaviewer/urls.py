from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import url, include
from rest_framework import routers
from django.shortcuts import redirect
from mysite.settings import IS_SYNCING
from axes.decorators import watch_login

from mediaviewer.views import (home,
                               files,
                               detail,
                               comment,
                               signin,
                               signout,
                               settings,
                               messaging,
                               requests,
                               waiterstatus,
                               password_reset,
                               waiter_display,
                               ajax,
                               )

router = routers.DefaultRouter()

urlpatterns = [
                       url(r'^$', home.home, name='home'),
                       #url(r'^files/$', lambda x: redirect('/mediaviewer/files/display/0/')),
                       #url(r'^files/display/(?P<items>\d+)/$', files.files, name='files'),
                       #url(r'^paths/$', lambda x: redirect('/mediaviewer/paths/display/0/')),
                       #url(r'^paths/display/(?P<items>\d+)/$', paths.paths, name='paths'),
                       #url(r'^errors/display/(?P<items>\d+)/$', errors.errors, name='errors'),
                       #url(r'^errors/$', lambda x: redirect('/mediaviewer/errors/display/50/')),
                       url(r'^files/(?P<file_id>\d+)/$', detail.filesdetail, name='filesdetail'),
                       url(r'^files/(?P<file_id>\d+)/comment/$', comment.comment, name='comment'),
                       url(r'^files/(?P<file_id>\d+)/results/$', comment.results, name='results'),
                       url(r'^paths/(?P<path_id>\d+)/$', detail.pathsdetail, name='pathsdetail'),
                       url(r'^tvshows/$', lambda x: redirect('/mediaviewer/tvshows/summary/')),
                       url(r'^tvshows/display/(?P<pathid>\d+)/$', files.tvshows, name='tvshows'),
                       url(r'^tvshows/(?P<pathid>\d+)/$', files.tvshows, name='tvshows'),
                       url(r'^tvshows/summary/$', files.tvshowsummary, name='tvshowsummary'),
                       url(r'^tvshows/genre/(?P<genre_id>\d+)/$', files.tvshows_by_genre, name='tvshows_by_genre'),
                       url(r'^movies/$', files.movies, name='movies'),
                       url(r'^movies/genre/(?P<genre_id>\d+)/$', files.movies_by_genre, name='movies_by_genre'),
                       url(r'^downloadlink/(?P<fileid>\d+)/$', detail.downloadlink, name='downloadlink'),
                       url(r'^login/', watch_login(signin.signin), name='signin'),
                       url(r'^logout/', signout.signout, name='signout'),
                       url(r'^settings/', settings.settings, name='settings'),
                       url(r'^submitsettings/', settings.submitsettings, name='submitsettings'),
                       url(r'^submitsitesettings/', settings.submitsitesettings, name='submitsitesettings'),
                       url(r'^submitnewuser/', settings.submitnewuser, name='submitnewuser'),
                       url(r'^submitsitewidemessage/', messaging.submitsitewidemessage, name='submitsitewidemessage'),
                       url(r'^waiterdisplay/(?P<fileid>\d+)/$', waiter_display.waiter_display, name='waiterdisplay'),
                       url(r'^requests/', requests.requests, name='requests'),
                       url(r'^addrequests/', requests.addrequests, name='addrequests'),
                       url(r'^ajaxviewed/', detail.ajaxviewed, name='ajaxviewed'),
                       url(r'^ajaxsuperviewed/', detail.ajaxsuperviewed, name='ajaxsuperviewed'),
                       url(r'^ajaxvote/', requests.ajaxvote, name='ajaxvote'),
                       url(r'^ajaxdone/', requests.ajaxdone, name='ajaxdone'),
                       url(r'^ajaxgiveup/', requests.ajaxgiveup, name='ajaxgiveup'),
                       url(r'^ajaxdownloadbutton/', detail.ajaxdownloadbutton, name='ajaxdownloadbutton'),
                       url(r'^ajaxwaiterstatus/', waiterstatus.ajaxwaiterstatus, name='ajaxwaiterstatus'),
                       url(r'^ajaxclosemessage/', messaging.ajaxclosemessage, name='ajaxclosemessage'),
                       url(r'^ajaxreport/', files.ajaxreport, name='ajaxreport'),
                       url(r'^ajaxrunscraper/', home.ajaxrunscraper, name='ajaxrunscraper'),
                       url(r'^ajaxvideoprogress/(?P<guid>[0-9A-Za-z]+)/(?P<hashed_filename>.+)/$', ajax.ajaxvideoprogress, name='ajaxvideoprogress'),
                       url(r'^ajaxgenres/(?P<guid>[0-9A-Za-z]+)/$', ajax.ajaxgenres, name='ajaxgenres'),
                       url(r'^user/reset/$',
                           password_reset.reset,
                           name='password_reset'),
                       url(r'^user/reset/done$',
                           password_reset.reset_done,
                           name='password_reset_done'),
                       url(r'^user/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           password_reset.reset_confirm,
                           name='password_reset_confirm'),
                       url(r'^user/create/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           password_reset.create_new_password,
                           name='password_create_confirm'),
                       url(r'^user/reset/complete$',
                           password_reset.reset_complete,
                           name='password_reset_complete'),
                       url(r'^user/change_password/$',
                           password_reset.change_password,
                           name='change_password'),
                       url(r'^user/change_password_submit/$',
                           password_reset.change_password_submit,
                           name='change_password_submit'),
                       ]

if not IS_SYNCING:
    from mediaviewer.api import (viewset,
                                 path_viewset,
                                 file_viewset)
    router.register(r'downloadtoken', viewset.DownloadTokenViewSet, base_name='downloadtoken')
    router.register(r'downloadclick', viewset.DownloadClickViewSet)
    router.register(r'unstreamablefile', file_viewset.UnstreamableFileViewSet, base_name='unstreamablefile')
    #router.register(r'file', file_viewset.FileViewSet, base_name='file')
    router.register(r'movie', file_viewset.MovieFileViewSet, base_name='movie')
    router.register(r'tv', file_viewset.TvFileViewSet, base_name='tv')
    #router.register(r'path', viewset.PathViewSet, base_name='path')
    router.register(r'tvpath', path_viewset.TvPathViewSet, base_name='tvpath')
    router.register(r'moviepath', path_viewset.MoviePathViewSet, base_name='moviepath')
    router.register(r'datatransmission', viewset.DataTransmissionViewSet)
    router.register(r'error', viewset.ErrorViewSet)
    router.register(r'message', viewset.MessageViewSet)
    router.register(r'filenamescrapeformat', viewset.FilenameScrapeFormatViewSet)
    router.register(r'posterfilebypath', viewset.PosterViewSetByPath)
    router.register(r'posterfilebyfile', viewset.PosterViewSetByFile)
    router.register(r'usercomment', viewset.UserCommentViewSet)

    urlpatterns += [url(r'^api/', include(router.urls, namespace='api')),
                    url(r'^api/inferscrapers/', csrf_exempt(viewset.InferScrapersView.as_view())),
                    #url(r'^api/posterviewsetbypath/', csrf_exempt(viewset.PosterViewSetByPath.as_view())),
                    ]
