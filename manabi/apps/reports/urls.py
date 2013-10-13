from django.conf.urls import *
from django.conf import settings

from manabi.apps.utils.views import direct_to_template


urlpatterns = patterns('manabi.apps.reports',
    url(r'^spring_break_usage$', 'views.spring_break_usage'),
)
