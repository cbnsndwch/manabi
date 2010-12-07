import os

from django.conf.urls.defaults import *
from django.conf import settings
from flashcards.models import SharedDeck, Deck, FactType, Card
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list, object_detail

#TODO rename REST to API


urlpatterns = patterns('flashcards',
    #TODO named URIs

    # New layout URIs
    (r'^add/$', 'views.add_decks',
        name='add_decks'),
    (r'^decks/(?P<deck_id>\d+)/$', 'views.deck_detail'), # object_detail, decks_dict), #TODO add permissions enforcement for viewing
    (r'^api/decks/(\w+)/subscribe/$', 'views.rest_deck_subscribe',
        name='api-subscribe_to_deck'),
    (r'^facts/(\w+)/subfacts', 'views.subfacts',
        name='fact_subfacts'),

    #(r'^$', 'views.index'),
    (r'^decks/$', 'views.deck_list',
        name='decks'),
    #(r'^decks/(\w+)', 'views.deck_show')
    (r'^decks/(\w+)/update/$', 'views.deck_update',
        name='update_deck'),
    (r'^decks/create/$', 'views.deck_create',
        name='create_deck'),
    (r'^decks/(\w+)/delete/$', 'views.deck_delete',
        name='delete_deck'),

    (r'^facts/$', 'views.facts_editor',
        name='facts'),
    (r'^facts/(\w+)/update', 'views.fact_update',
        name='update_fact'),
    
    #REST
    #(r'^api$', 'views.rest_entry_point'),
    (r'^api/generate_reading/$', 'views.rest_generate_reading',
        name='api-generate_reading'),
    (r'^api/decks/$', 'views.rest_decks',
        name='api-decks'),
    (r'^api/decks/(\w+)/$', 'views.rest_deck',
        name='api-deck'), #POST: can set 'shared' field
    (r'^api/decks_with_totals/$', 'views.rest_decks_with_totals',
        name='api-decks_with_totals'),
    (r'^api/fact_types/$', 'views.rest_fact_types',
        name='api-fact_types'),
    (r'^api/fact_types/(\w+)/card_templates/$', 'views.rest_card_templates'),
    (r'^api/fact_types/(\w+)/fields/$', 'views.rest_fields',
        name='api-fact_type_fields'),
    (r'^api/facts/$', 'views.rest_facts',
        name='api-facts'),
    (r'^api/facts/tags/$', 'views.rest_facts_tags',
        name='api-fact_tags'),
    (r'^api/facts/(\w+)/$', 'views.rest_fact'),
    (r'^api/facts/(\w+)/suspend/$', 'views.rest_fact_suspend'),
    (r'^api/facts/(\w+)/unsuspend/$', 'views.rest_fact_unsuspend'),
    (r'^api/facts/(\w+)/card_templates/$', 'views.rest_card_templates_for_fact'), #TODO should be a query on /card_templates instead? ?fact=1&activated=true
    (r'^api/cards/$', 'views.rest_cards',
        name='api-cards'),
    (r'^api/cards/(\w+)/$', 'views.rest_card',
        name='api-card'),
    #(r'^api/cards/(\w+)/suspend$', 'views.rest_card_suspend'),
    #(r'^ajax/decks$', 'views.decks'),
    #(r'^ajax/decks/(\w+)/facts$', 'views.facts'),
    #(r'^ajax/fact_types/(\w+)/facts$', 'views.facts_of_type'),


    #card reviewing
    (r'^api/cards_for_review/due_count/$', 'views.due_card_count',
        name='api-due_card_count'),
    (r'^api/cards_for_review/new_count/$', 'views.new_card_count',
        name='api-due_card_count'),
    (r'^api/cards_for_review/due_tomorrow_count/$', 'views.cards_due_tomorrow_count',
        name='api-due_tomorrow_count'),
    (r'^api/cards_for_review/next_due_at/$', 'views.next_card_due_at',
        name='api-next_card_due_at'),
    (r'^api/cards_for_review/hours_until_next_due/$', 'views.hours_until_next_card_due',
        name='hours_until_next_card_due'),
    (r'^api/cards_for_review/$', 'views.next_cards_for_review',
        name='api-next_cards_for_review'),

    #card review undo
    (r'^api/cards_for_review/undo/$', 'views.undo_review',
        name='undo_review'),
    (r'^api/cards_for_review/undo/reset/$', 'views.reset_review_undo_stack',
        name='reset_review_undo_stack'),

    

    #url(r'^$', direct_to_template, {"template": "flashcards/base.html"}, name="flashcards"),
)


#if settings.DEBUG:
#    # serving the media files for dojango / dojo (js/css/...)
#    urlpatterns += patterns('',
#        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
#            {'document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'media'))}),
#    )
