from django.conf.urls import *


urlpatterns = [
    url(r'^$', 'manabi.apps.importer.views.importer'),
]
