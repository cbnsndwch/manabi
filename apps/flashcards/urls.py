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
    url(r'^decks/(?P<deck_id>\d+)/$', 'deck_detail'), 
    url(r'^decks/$', 'deck_list',
        name='decks'),
    url(r'^decks/(\w+)/update/$', 'deck_update',
        name='update_deck'),
    url(r'^decks/create/$', 'deck_create',
        name='create_deck'),
    url(r'^decks/(\w+)/delete/$', 'deck_delete',
        name='delete_deck'),

    url(r'^facts/$', 'facts_editor',
        name='facts'),
    url(r'^facts/(\w+)/update', 'fact_update',
        name='update_fact'),
)

# Views that return Dojo templates
# (because some things are easier done without all-out xhr)
#urlpatterns += patterns('flashcards.views.dojo',
    #url(r'^dojo-templates/SessionOverDialog.html$', 'session_over_dialog',
        #name='dojo-session_over_dialog'),
#)
        

# RESTy API
urlpatterns += patterns('flashcards.views.api',
    url(r'^api/decks/(\w+)/subscribe/$', 'rest_deck_subscribe',
        name='api-subscribe_to_deck'),
    #url(r'^api$', 'rest_entry_point'),
    url(r'^api/generate_reading/$', 'rest_generate_reading',
        name='api-generate_reading'),
    url(r'^api/decks/$', 'rest_decks',
        name='api-decks'),
    url(r'^api/decks/(\w+)/$', 'rest_deck',
        name='api-deck'), #POST: can set 'shared' field
    url(r'^api/fact_types/$', 'rest_fact_types',
        name='api-fact_types'),
    url(r'^api/fact_types/(\w+)/card_templates/$', 'rest_card_templates'),
    url(r'^api/fact_types/(\w+)/fields/$', 'rest_fields',
        name='api-fact_type_fields'),
    url(r'^api/facts/$', 'rest_facts',
        name='api-facts'),
    url(r'^api/facts/tags/$', 'rest_facts_tags',
        name='api-fact_tags'),
    url(r'^api/facts/(\w+)/$', 'rest_fact'),
    url(r'^api/facts/(\w+)/suspend/$', 'rest_fact_suspend'),
    url(r'^api/facts/(\w+)/unsuspend/$', 'rest_fact_unsuspend'),

    #TODO should be a query on /card_templates instead? ?fact=1&activated=true
    url(r'^api/facts/(\w+)/card_templates/$',
        'rest_card_templates_for_fact'), 
    url(r'^api/cards/$', 'rest_cards',
        name='api-cards'),
)

urlpatterns += patterns('flashcards.views.api.review',
    url(r'^facts/(\w+)/subfacts', 'subfacts',
        name='fact_subfacts'),

    url(r'^api/cards/(\w+)/$', 'rest_card',
        name='api-card'),
    url(r'^api/cards_for_review/due_count/$', 'due_card_count',
        name='api-due_card_count'),
    url(r'^api/cards_for_review/new_count/$', 'new_card_count',
        name='api-new_card_count'),
    url(r'^api/cards_for_review/due_tomorrow_count/$', 'due_tomorrow_count',
        name='api-due_tomorrow_count'),
    url(r'^api/cards_for_review/next_due_at/$', 'next_card_due_at',
        name='api-next_card_due_at'),
    url(r'^api/cards_for_review/hours_until_next_due/$', 'hours_until_next_card_due',
        name='api-hours_until_next_card_due'),
    url(r'^api/next_cards_for_review/$', 'next_cards_for_review',
        name='api-next_cards_for_review'),

    #card review undo
    url(r'^api/cards_for_review/undo/$', 'undo_review',
        name='api-undo_review'),
    url(r'^api/cards_for_review/undo/reset/$', 'reset_review_undo_stack',
        name='api-reset_review_undo_stack'),

)

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
