from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
#from abb import views
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^vbb/', include('vbb.urls')),
    url(r'^abb/', include('abb.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^def/', 'abb.views.init'),
    url(r'^test/(?P<tab>\d+)/$', 'vbb.views.test'),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
