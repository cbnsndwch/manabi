import os

from django.conf.urls.defaults import *
from django.conf import settings
from flashcards.models import SharedDeck, Deck, FactType, Card
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list, object_detail



urlpatterns = patterns('flashcards.views.crud',
    #(r'^$', 'views.index'),
    #url(r'^$', direct_to_template, {"template": "flashcards/base.html"}, name="flashcards"),
    (r'^add/$', 'add_decks',
        name='add_decks'),

    #TODO add permissions enforcement for viewing
    (r'^decks/(?P<deck_id>\d+)/$', 'deck_detail'), 
    (r'^decks/$', 'deck_list',
        name='decks'),
    (r'^decks/(\w+)/update/$', 'deck_update',
        name='update_deck'),
    (r'^decks/create/$', 'deck_create',
        name='create_deck'),
    (r'^decks/(\w+)/delete/$', 'deck_delete',
        name='delete_deck'),

    (r'^facts/$', 'facts_editor',
        name='facts'),
    (r'^facts/(\w+)/update', 'fact_update',
        name='update_fact'),
)

# RESTy API
urlpatterns += patterns('flashcards.views.api',
    (r'^api/decks/(\w+)/subscribe/$', 'rest_deck_subscribe',
        name='api-subscribe_to_deck'),
    #(r'^api$', 'rest_entry_point'),
    (r'^api/generate_reading/$', 'rest_generate_reading',
        name='api-generate_reading'),
    (r'^api/decks/$', 'rest_decks',
        name='api-decks'),
    (r'^api/decks/(\w+)/$', 'rest_deck',
        name='api-deck'), #POST: can set 'shared' field
    (r'^api/decks_with_totals/$', 'rest_decks_with_totals',
        name='api-decks_with_totals'),
    (r'^api/fact_types/$', 'rest_fact_types',
        name='api-fact_types'),
    (r'^api/fact_types/(\w+)/card_templates/$', 'rest_card_templates'),
    (r'^api/fact_types/(\w+)/fields/$', 'rest_fields',
        name='api-fact_type_fields'),
    (r'^api/facts/$', 'rest_facts',
        name='api-facts'),
    (r'^api/facts/tags/$', 'rest_facts_tags',
        name='api-fact_tags'),
    (r'^api/facts/(\w+)/$', 'rest_fact'),
    (r'^api/facts/(\w+)/suspend/$', 'rest_fact_suspend'),
    (r'^api/facts/(\w+)/unsuspend/$', 'rest_fact_unsuspend'),

    #TODO should be a query on /card_templates instead? ?fact=1&activated=true
    (r'^api/facts/(\w+)/card_templates/$', 'rest_card_templates_for_fact'), 
    (r'^api/cards/$', 'rest_cards',
        name='api-cards'),
    (r'^api/cards/(\w+)/$', 'rest_card',
        name='api-card'),
)

urlpatterns += patterns('flashcards.views.api.review',
    (r'^facts/(\w+)/subfacts', 'subfacts',
        name='fact_subfacts'),

    (r'^api/cards_for_review/due_count/$', 'due_card_count',
        name='api-due_card_count'),
    (r'^api/cards_for_review/new_count/$', 'new_card_count',
        name='api-due_card_count'),
    (r'^api/cards_for_review/due_tomorrow_count/$', 'cards_due_tomorrow_count',
        name='api-due_tomorrow_count'),
    (r'^api/cards_for_review/next_due_at/$', 'next_card_due_at',
        name='api-next_card_due_at'),
    (r'^api/cards_for_review/hours_until_next_due/$', 'hours_until_next_card_due',
        name='hours_until_next_card_due'),
    (r'^api/cards_for_review/$', 'next_cards_for_review',
        name='api-next_cards_for_review'),

    #card review undo
    (r'^api/cards_for_review/undo/$', 'undo_review',
        name='undo_review'),
    (r'^api/cards_for_review/undo/reset/$', 'reset_review_undo_stack',
        name='reset_review_undo_stack'),

)


#if settings.DEBUG:
#    # serving the media files for dojango / dojo (js/css/...)
#    urlpatterns += patterns('',
#        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
#            {'document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'media'))}),
#    )
