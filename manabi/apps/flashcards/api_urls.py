from django.conf import settings
from django.conf.urls import *

from manabi.apps.flashcards import api


urlpatterns = patterns(
    'manabi.apps.flashcards.api',

    url(r'^next_cards_for_review/$', api.NextCardsForReview.as_view())
)

