from django.conf.urls import patterns, url

from vbb import views

urlpatterns = patterns('',
    url(r'^(?P<eid>\w+)/$', views.index),
	url(r'^$', views.empty)
)
