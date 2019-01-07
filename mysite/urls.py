from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'site.views.home', name='home'),
    # url(r'^site/', include('site.foo.urls')),
    # (r'^cache/', include('django_memcached.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
    url(r'^mediaviewer/',
        include(('mediaviewer.urls', 'mediaviewer'), namespace='mediaviewer')),
]
