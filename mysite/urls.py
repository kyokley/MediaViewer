from django.conf import settings as conf_settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import re_path

admin.autodiscover()

urlpatterns = [
    # Examples:
    # re_path(r'^$', 'site.views.home', name='home'),
    # re_path(r'^site/', include('site.foo.urls')),
    # (r'^cache/', include('django_memcached.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path("grappelli/", include("grappelli.urls")),  # grappelli URLS
    # Uncomment the next line to enable the admin:
    re_path(r"^admin/", admin.site.urls),
    re_path(
        r"^mediaviewer/",
        include(("mediaviewer.urls", "mediaviewer"), namespace="mediaviewer"),
    ),
] + static(conf_settings.MEDIA_URL, document_root=conf_settings.MEDIA_ROOT)

if conf_settings.USE_SILK:
    urlpatterns += [re_path(r"^silk/", include("silk.urls", namespace="silk"))]
