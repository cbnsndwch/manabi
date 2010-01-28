import os

from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.simple import direct_to_template

from django.views.generic.list_detail import object_list

urlpatterns = patterns('flashcards',
    #TODO named URIs
    #(r'^$', 'views.index'),
    (r'^decks$', 'views.deck_list'),
    #(r'^decks/(\w+)', 'views.deck_show')
    (r'^decks/(\w+)/update$', 'views.deck_update'),
    (r'^decks/create$', 'views.deck_create'),
    (r'^decks/(\w+)/create$', 'views.deck_create'),
    (r'^decks/(\w+)/delete$', 'views.deck_delete'),

    #shared decks
    #(r'^shared_decks$', 'views.shared_deck_list'),
    (r'^shared_decks/(\w+)/download$', 'views.shared_deck_download'),
    (r'^decks/(\w+)/share$', 'views.deck_share'),
    (r'^shared_decks$', 'views.shared_deck_list'),

    (r'^facts$', 'views.facts_editor'),
    (r'^facts/(\w+)/update', 'views.fact_update'),
    
    #REST
    (r'^rest$', 'views.rest_entry_point'),
    (r'^rest/generate_reading$', 'views.rest_generate_reading'),
    (r'^rest/decks$', 'views.rest_decks'),
    (r'^rest/decks/(\w+)$', 'views.rest_deck'),
    (r'^rest/decks_with_totals$', 'views.rest_decks_with_totals'),
    (r'^rest/fact_types$', 'views.rest_fact_types'),
    (r'^rest/fact_types/(\w+)/card_templates$', 'views.rest_card_templates'),
    (r'^rest/fact_types/(\w+)/fields$', 'views.rest_fields'),
    (r'^rest/facts$', 'views.rest_facts'),
    (r'^rest/facts/tags$', 'views.rest_facts_tags'),
    (r'^rest/facts/(\w+)$', 'views.rest_fact'),
    (r'^rest/facts/(\w+)/suspend$', 'views.rest_fact_suspend'),
    (r'^rest/facts/(\w+)/unsuspend$', 'views.rest_fact_unsuspend'),
    (r'^rest/facts/(\w+)/card_templates$', 'views.rest_card_templates_for_fact'), #TODO should be a query on /card_templates instead? ?fact=1&activated=true
    (r'^rest/cards$', 'views.rest_cards'),
    (r'^rest/cards/(\w+)$', 'views.rest_card'),
    #(r'^rest/cards/(\w+)/suspend$', 'views.rest_card_suspend'),
    #(r'^ajax/decks$', 'views.decks'),
    #(r'^ajax/decks/(\w+)/facts$', 'views.facts'),
    #(r'^ajax/fact_types/(\w+)/facts$', 'views.facts_of_type'),


    #card reviewing
    (r'^rest/cards_for_review/due_count$', 'views.cards_due_count'),
    (r'^rest/cards_for_review/new_count$', 'views.cards_new_count'),
    (r'^rest/cards_for_review/due_tomorrow_count$', 'views.cards_due_tomorrow_count'),
    (r'^rest/cards_for_review/next_due_at$', 'views.next_card_due_at'),
    (r'^rest/cards_for_review/hours_until_next_due$', 'views.hours_until_next_card_due'),
    (r'^rest/cards_for_review$', 'views.next_cards_for_review'),
    

    #url(r'^$', direct_to_template, {"template": "flashcards/base.html"}, name="flashcards"),
)

#if settings.DEBUG:
#    # serving the media files for dojango / dojo (js/css/...)
#    urlpatterns += patterns('',
#        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
#            {'document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'media'))}),
#    )
