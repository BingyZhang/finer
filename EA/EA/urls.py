from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^bds/', 'auth.views.login'),
    url(r'^vote/(?P<eid>\w+)/$', 'auth.views.vote'),
    url(r'^def/', include('elect_def.urls')),
    url(r'^admin/', include(admin.site.urls)),                   
)
