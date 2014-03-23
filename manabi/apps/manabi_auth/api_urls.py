from django.conf.urls import *

from manabi.apps.manabi_auth import api


urlpatterns = patterns(
    'manabi.apps.manabi_auth.api',

    url(r'^authentication_status/$', api.AuthenticationStatus.as_view()),
    url(r'^users/$', api.User.as_view()),
)

