from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.simple import direct_to_template


urlpatterns = patterns('reports',
    url(r'^spring_break_usage$', 'views.spring_break_usage'),
)
