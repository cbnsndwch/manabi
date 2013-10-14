import os

from django.conf import settings
from django.conf.urls import *
from django.views.decorators.cache import cache_page
from manabi.apps.utils.views import direct_to_template

from manabi.apps.flashcards.models import Deck, FactType, Card
from manabi.apps.flashcards import redis_listeners


urlpatterns = patterns('manabi.apps.flashcards.views.crud',
    url(r'^add/$', 'add_decks',
        name='add_decks'),

    #TODO-OLD add permissions enforcement for viewing
    url(r'^decks/(?P<deck_id>\d+)/$', 'deck_detail',
        name='deck_detail'), 
    url(r'^decks/$', 'deck_list',
        name='decks'),
    url(r'^decks/(\w+)/update/$', 'deck_update',
        name='update_deck'),
    url(r'^decks/create/$', 'deck_create',
        name='create_deck'),
    url(r'^decks/(\w+)/delete/$', 'deck_delete',
        name='delete_deck'),


    url(r'^decks/(\w+)/exported-csv/$', 'deck_export_to_csv',
        name='exported_deck_csv'),

    url(r'^facts/$', 'facts_editor',
        name='facts'),
    url(r'^facts/(\w+)/update/$', 'fact_update',
        name='update_fact'),
)


urlpatterns += patterns('manabi.apps.books.views',
    url(r'^decks/(?P<deck_id>\d+)/textbook-source/$', 'deck_textbook_source',
        name='deck_textbook_source'),
)



# kinda-sorta-RESTy API
internal_api_urlpatterns = patterns('manabi.apps.flashcards.views.api',
    url(r'^decks/(\w+)/subscribe/$', 'rest_deck_subscribe',
        name='api-subscribe_to_deck'),
    #url(r'^api$', 'rest_entry_point'),
    url(r'^generate_reading/$', 'rest_generate_reading',
        name='api-generate_reading'),
    #url(r'^decks/$', 'rest_decks',
    #    name='api-decks'),
    
    url(r'^decks/(\w+)/name/$', 'rest_deck_name',
        name='api-deck_name'),
    url(r'^decks/(\w+)/description/$', 'rest_deck_description',
        name='api-deck_description'),
    url(r'^decks/(\w+)/$', 'rest_deck',
        name='api-deck'), #POST: can set 'shared' field

    url(r'^fact_types/$', 'rest_fact_types',
        name='api-fact_types'),
    url(r'^fact_types/(\w+)/card_templates/$', 'rest_card_templates'),
    url(r'^fact_types/(\w+)/fields/$', 'rest_fields',
        name='api-fact_type_fields'),
    url(r'^facts/$', 'rest_facts',
        name='api-facts'),
    url(r'^facts/tags/$', 'rest_facts_tags',
        name='api-fact_tags'),
    url(r'^facts/(\w+)/$', 'rest_fact'),
    url(r'^facts/(\w+)/suspend/$', 'rest_fact_suspend'),
    url(r'^facts/(\w+)/unsuspend/$', 'rest_fact_unsuspend'),


    #TODO-OLD should be a query on /card_templates instead? ?fact=1&activated=true
    url(r'^facts/(\w+)/card_templates/$',
        'rest_card_templates_for_fact'), 
    url(r'^cards/$', 'rest_cards',
        name='api-cards'),

)


internal_api_urlpatterns += patterns('manabi.apps.flashcards.views.api.review',
    url(r'^facts/(\w+)/subfacts/$', 'subfacts',
        name='fact_subfacts'),

    url(r'^cards/(\w+)/$', 'rest_card',
        name='api-card'),
    url(r'^cards_for_review/due_count/$', 'due_card_count',
        name='api-due_card_count'),
    url(r'^cards_for_review/next_due_at/$', 'next_card_due_at',
        name='api-next_card_due_at'),
    url(r'^cards_for_review/hours_until_next_due/$', 'hours_until_next_card_due',
        name='api-hours_until_next_card_due'),

    #card review undo
    url(r'^cards_for_review/undo/$', 'undo_review',
        name='api-undo_review'),
    url(r'^cards_for_review/undo/reset/$', 'reset_review_undo_stack',
        name='api-reset_review_undo_stack'),

)



# Actual REST API
from manabi.apps.flashcards.views.rest import *
rest_api_urlpatterns = patterns('',
    url(r'^$', EntryPoint.as_view(),
        name='rest-entry_point'),

    url(r'^decks/$', DeckList.as_view(),
        name='rest-deck_list'),
    url(r'^shared-decks/$', SharedDeckList.as_view(),
        name='rest-shared_deck_list'),
    url(r'^decks/(?P<pk>\d+)/subscriptions/$', DeckSubscription.as_view(),
        name='rest-deck_subscription'),
    url(r'^decks/(?P<pk>\d+)/status/$', DeckStatus.as_view(),
        name='rest-deck_status'),
    url(r'^decks/(?P<pk>\d+)/$', Deck.as_view(),
        name='rest-deck'),

    url(r'^decks/all/$', AllDecks.as_view(),
        name='rest-all_decks'),

    url(r'^next-cards-for-review/$', NextCardsForReview.as_view(),
        name='rest-next_cards_for_review'),
    url(r'^next-cards-for-review/undo-stack/$', ReviewUndo.as_view(),
        name='rest-review_undo_stack'),

    url(r'^cards/(?P<pk>\d+)/reviews/$', CardReviews.as_view(),
        name='rest-card_reviews'),
    url(r'^cards/(?P<pk>\d+)/$', Card.as_view(),
        name='rest-card'),
)


urlpatterns += patterns('',
    url(r'^internal-api/', include(internal_api_urlpatterns)),
)


