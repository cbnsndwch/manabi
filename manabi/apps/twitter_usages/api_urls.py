from django.conf.urls import *

from manabi.apps.twitter_usages import api


urlpatterns = patterns(
    'manabi.apps.twitter_usages.api',

    url(r'^fact/(?P<fact>\w+)/tweets/$', api.FactTweets.as_view(),
        name='api_fact_tweets'),
)
