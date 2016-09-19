from django.conf.urls import url

from manabi.apps.twitter_usages.api_views import (
    TweetsForFactView,
)

urlpatterns = [
    url('tweets_for_fact/(?P<fact_id>\d+)/$', TweetsForFactView.as_view()),
]
