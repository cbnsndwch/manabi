import os

from django.conf.urls.defaults import *
from django.conf import settings
from flashcards.models import Deck, FactType, Card
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list, object_detail




urlpatterns = patterns('flashcards.views.crud',
    #url(r'^$', 'views.index'),
    #urlurl(r'^$', direct_to_template, {"template": "flashcards/base.html"}, name="flashcards"),
    url(r'^add/$', 'add_decks',
        name='add_decks'),

    #TODO add permissions enforcement for viewing
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



# kinda-sorta-RESTy API
internal_api_urlpatterns = patterns('flashcards.views.api',
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


    #TODO should be a query on /card_templates instead? ?fact=1&activated=true
    url(r'^facts/(\w+)/card_templates/$',
        'rest_card_templates_for_fact'), 
    url(r'^cards/$', 'rest_cards',
        name='api-cards'),

)


internal_api_urlpatterns += patterns('flashcards.views.api.review',
    url(r'^facts/(\w+)/subfacts/$', 'subfacts',
        name='fact_subfacts'),

    url(r'^cards/(\w+)/$', 'rest_card',
        name='api-card'),
    url(r'^cards_for_review/due_count/$', 'due_card_count',
        name='api-due_card_count'),
    url(r'^cards_for_review/new_count/$', 'new_card_count',
        name='api-new_card_count'),
    url(r'^cards_for_review/due_tomorrow_count/$', 'due_tomorrow_count',
        name='api-due_tomorrow_count'),
    url(r'^cards_for_review/next_due_at/$', 'next_card_due_at',
        name='api-next_card_due_at'),
    url(r'^cards_for_review/hours_until_next_due/$', 'hours_until_next_card_due',
        name='api-hours_until_next_card_due'),
    url(r'^next_cards_for_review/$', 'next_cards_for_review',
        name='api-next_cards_for_review'),

    #card review undo
    url(r'^cards_for_review/undo/$', 'undo_review',
        name='api-undo_review'),
    url(r'^cards_for_review/undo/reset/$', 'reset_review_undo_stack',
        name='api-reset_review_undo_stack'),

)



# Actual REST API
from flashcards.views.rest import *
rest_api_urlpatterns = patterns('',
    url(r'^$', EntryPoint.as_view(),
        name='rest-entry_point'),

    url(r'^decks/$', DeckList.as_view(),
        name='rest-deck_list'),
    url(r'^shared-decks/$', SharedDeckList.as_view(),
        name='rest-shared_deck_list'),
    url(r'^decks/(?P<pk>\d+)/$', Deck.as_view(),
        name='rest-deck'),
    url(r'^decks/(?P<pk>\d+)/subscriptions/$', DeckSubscription.as_view(),
        name='rest-deck_subscription'),
)


urlpatterns += patterns('',
    url(r'^internal-api/', include(internal_api_urlpatterns)),
)


# Dynamic ...static files
urlpatterns += patterns('',
    url(r'^flashcards.js$', direct_to_template,
        { 'template': 'flashcards/flashcards.js',
          'mimetype': 'text/javascript', },
        name='flashcards-js'),
    url(r'^reviews.js$', direct_to_template,
        { 'template': 'flashcards/reviews.js',
          'mimetype': 'text/javascript', },
        name='reviews-js'),
    url(r'^reviews_ui.js$', direct_to_template,
        { 'template': 'flashcards/reviews_ui.js',
          'mimetype': 'text/javascript', },
        name='reviews-ui-js'),
)


#if settings.DEBUG:
   ## serving the media files for dojango / dojo (js/css/...)
   #urlpatterns += patterns('',
       #url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
           #{'document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'media'))}),
   #)
