from django.conf.urls import *

from manabi.apps.flashcards import api


urlpatterns = patterns(
    'manabi.apps.flashcards.api',

    url(r'^next_cards_for_review/$', api.NextCardsForReview.as_view()),
    url(r'^cards/(?P<card>\w+)/$', api.Card.as_view(), name='api_card'),
    url(r'^cards/(?P<card>\w+)/review/$', api.CardReview.as_view(), name='api_card_review'),

    url(r'^decks/$', api.Decks.as_view(), name='api_decks'),
    url(r'^shared_decks/$', api.SharedDecks.as_view(), name='api_shared_decks'),
)

