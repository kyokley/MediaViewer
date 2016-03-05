from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import patterns, url, include
from rest_framework import routers
from django.shortcuts import redirect
from mysite.settings import IS_SYNCING

from mediaviewer.views import (home,
                               files,
                               paths,
                               datausage,
                               detail,
                               userusage,
                               errors,
                               comment,
                               signin,
                               signout,
                               settings,
                               messaging,
                               requests,
                               waiterstatus,
                               )

router = routers.DefaultRouter()

urlpatterns = patterns('',
                       url(r'^$', home.home, name='home'),
                       url(r'^files/$', lambda x: redirect('/mediaviewer/files/display/0/')),
                       url(r'^files/display/(?P<items>\d+)/$', files.files, name='files'),
                       url(r'^paths/$', lambda x: redirect('/mediaviewer/paths/display/0/')),
                       url(r'^paths/display/(?P<items>\d+)/$', paths.paths, name='paths'),
                       url(r'^datausage/display/(?P<items>\d+)/$', datausage.datausage, name='datausage'),
                       url(r'^datausage/$', lambda x: redirect('/mediaviewer/datausage/display/50/')),
                       url(r'^userusage/$', userusage.userusage, name='userusage'),
                       url(r'^errors/display/(?P<items>\d+)/$', errors.errors, name='errors'),
                       url(r'^errors/$', lambda x: redirect('/mediaviewer/errors/display/50/')),
                       url(r'^files/(?P<file_id>\d+)/$', detail.filesdetail, name='filesdetail'),
                       url(r'^files/(?P<file_id>\d+)/comment/$', comment.comment, name='comment'),
                       url(r'^files/(?P<file_id>\d+)/results/$', comment.results, name='results'),
                       url(r'^paths/(?P<path_id>\d+)/$', detail.pathsdetail, name='pathsdetail'),
                       url(r'^tvshows/$', lambda x: redirect('/mediaviewer/tvshows/summary/')),
                       url(r'^tvshows/display/(?P<pathid>\d+)/$', files.tvshows, name='tvshows'),
                       url(r'^tvshows/(?P<pathid>\d+)/$', files.tvshows, name='tvshows'),
                       url(r'^tvshows/summary/$', files.tvshowsummary, name='tvshowsummary'),
                       url(r'^movies/$', lambda x: redirect('/mediaviewer/movies/display/0/')),
                       url(r'^movies/display/(?P<items>\d+)/$', files.movies, name='movies'),
                       url(r'^login/', signin.signin, name='signin'),
                       url(r'^logout/', signout.signout, name='signout'),
                       url(r'^settings/', settings.settings, name='settings'),
                       url(r'^submitsettings/', settings.submitsettings, name='submitsettings'),
                       url(r'^submitsitesettings/', settings.submitsitesettings, name='submitsitesettings'),
                       url(r'^submitsitewidemessage/', messaging.submitsitewidemessage, name='submitsitewidemessage'),
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
                       )

if not IS_SYNCING:
    from mediaviewer.api import viewset
    router.register(r'downloadtoken', viewset.DownloadTokenViewSet)
    router.register(r'downloadclick', viewset.DownloadClickViewSet)
    router.register(r'unstreamablefile', viewset.UnstreamableFileViewSet, base_name='unstreamablefile')
    router.register(r'file', viewset.FileViewSet, base_name='file')
    router.register(r'movie', viewset.MovieFileViewSet, base_name='movie')
    router.register(r'path', viewset.PathViewSet)
    router.register(r'datatransmission', viewset.DataTransmissionViewSet)
    router.register(r'error', viewset.ErrorViewSet)
    router.register(r'message', viewset.MessageViewSet)
    router.register(r'filenamescrapeformat', viewset.FilenameScrapeFormatViewSet)

    urlpatterns += [url(r'^api/', include(router.urls)),
                    url(r'^api/inferscrapers/', csrf_exempt(viewset.InferScrapersView.as_view())),
                    ]
