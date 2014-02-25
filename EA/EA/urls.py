from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^login/', 'auth.views.login'),
    url(r'^def/', include('elect_def.urls')),
    url(r'^admin/', include(admin.site.urls)),                   
)
