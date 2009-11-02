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
    
    #REST
    (r'^rest$', 'views.rest_entry_point'),
    (r'^rest/decks$', 'views.rest_decks'),
    (r'^rest/decks/(\w+)$', 'views.rest_deck'),
    (r'^rest/fact_types$', 'views.rest_fact_types'),
    (r'^rest/fact_types/(\w+)/card_templates$', 'views.rest_card_templates'),
    (r'^rest/fact_types/(\w+)/fields$', 'views.rest_fields'),
    (r'^rest/facts$', 'views.rest_facts'),
    (r'^rest/facts/(\w+)$', 'views.rest_fact'),
    (r'^rest/facts/(\w+)/card_templates$', 'views.rest_card_templates_for_fact'), #TODO should be a query on /card_templates instead? ?fact=1&activated=true
    (r'^rest/cards$', 'views.rest_cards'),
    (r'^rest/cards/(\w+)$', 'views.rest_card'),
    #(r'^ajax/decks$', 'views.decks'),
    #(r'^ajax/decks/(\w+)/facts$', 'views.facts'),
    #(r'^ajax/fact_types/(\w+)/facts$', 'views.facts_of_type'),


    #card reviewing
    (r'^rest/cards_for_review$', 'views.next_cards_for_review'),
    

    #(r'^$', 'views.base'),
    #(r'^decks$', 'views.deck_list'),
    #(r'^decks/(\w+)/update$', 'views.deck_update'),
    #(r'^decks/(\w+)/delete$', 'views.deck_delete'),
    #(r'^decks/create$', 'views.deck_create'),
    #(r'^ajax/fact_types$', 'views.fact_types'),
    #(r'^ajax/decks$', 'views.decks'),
    #(r'^ajax/decks/(\w+)/facts$', 'views.facts'),
    #(r'^ajax/fact_types/(\w+)/card_templates$', 'views.card_templates'),
    #(r'^ajax/fact_types/(\w+)/facts$', 'views.facts_of_type'),
    #(r'^ajax/fact_types/(\w+)/fields$', 'views.fields'),
    #(r'^ajax/fact_types/(\w+)/fields$', 'views.fields'),
    
    #url(r'^$', direct_to_template, {"template": "flashcards/base.html"}, name="flashcards"),
    #(r'^test/$', 'views.test'),
    #(r'^test/countries/$', 'views.test_countries'),
    #(r'^test/states/$', 'views.test_states'),
)

#if settings.DEBUG:
#    # serving the media files for dojango / dojo (js/css/...)
#    urlpatterns += patterns('',
#        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
#            {'document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'media'))}),
#    )
