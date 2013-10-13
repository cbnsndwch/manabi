from django.conf.urls import *

urlpatterns = patterns('manabi.apps.importer.views',
    url(r'^$', 'importer'),
)

