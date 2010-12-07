from decorators import all_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import naturalday
from django.db import transaction
from django.forms import forms
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.template.loader import render_to_string
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from models import Card
from models.constants import GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY
from models import NEW_CARDS_PER_DAY
from flashcards.models.undo import UndoCardReview
from decorators import has_card_query_filters
import datetime
import string
import subprocess



     ################################
  ######################################  
 ##                                    ## 
###        > Flashcard Review <        ###
 ##                                    ## 
  ######################################  
     ###############################

@login_required
def subfacts(request, parent_fact_id):
    parent_fact = get_object_or_404(Fact, pk=parent_fact_id)
    context = {'subfacts': parent_fact.subfacts.all()}
    return render_to_response('flashcards/subfacts.html', context)


@login_required
@json_response
@has_card_query_filters
def next_cards_for_review(request, deck=None, tags=None):
    if request.method == 'GET':
        count = int(request.GET.get('count', 5))

        # New cards per day limit.
        #TODO implement this to be user-configurable instead of hard-coded
        daily_new_card_limit = NEW_CARDS_PER_DAY

        # Early Review
        early_review = request.GET.get('early_review', 'false').lower() == 'true'

        # Learn More new cards. Usually this will be combined with early_review.
        learn_more = request.GET.get('learn_more', 'false').lower() == 'true'
        if learn_more:
            # Overrides the daily new card limit
            daily_new_card_limit = None

        # Beginning of review session?
        session_start = string.lower(request.GET.get('session_start', 'false')) == 'true'

        #try:
        excluded_card_ids = [int(e) for e in request.GET.get('excluded_cards', '').split()]
        #except ValueError:
            #excluded_card_ids = []

        next_cards = Card.objects.next_cards(request.user, count, excluded_card_ids, session_start, \
                deck=deck, tags=tags, early_review=early_review, daily_new_card_limit=daily_new_card_limit)
        #FIXME need to account for 0 cards returned 


        # format into json object
        formatted_cards = []
        reviewed_at = datetime.datetime.utcnow()
        for card in next_cards:
            card_context = {
                    'card': card,
                    'fields': card.fact.field_contents,
                    'fact': card.fact,
                    'card_back_template': card.template.back_template_name,
            }
            formatted_cards.append({
                    'id': card.id,
                    'fact_id': card.fact_id,
                    'front': card.render_front(),
                    'back': render_to_string('flashcards/card_back.html', card_context),
                    'next_due_at_per_grade': card.due_at_per_grade(reviewed_at=reviewed_at),
             })

        ret = {'success': True, 'cards': formatted_cards}
        return ret


@json_response
@login_required
def due_card_count(request):
    return Card.objects.due_cards(request.user).count()

@json_response
@login_required
def new_card_count(request):
    return Card.objects.new_cards(request.user).count()


#(r'^rest/cards_for_review/due_tomorrow_count$', 'views.cards_due_tomorrow_count'),
#(r'^rest/cards_for_review/next_card_due_at$', 'views.next_card_due_at'),



@json_response
@login_required
@has_card_query_filters
def due_tomorrow_count(request, deck=None, tags=None):
    return Card.objects.count_of_cards_due_tomorrow(request.user, deck=deck, tags=tags)

@json_response
@login_required
@has_card_query_filters
def hours_until_next_card_due(request, deck=None, tags=None):
    due_at = Card.objects.next_card_due_at(request.user, deck=deck, tags=tags)
    difference = due_at - datetime.datetime.utcnow()
    hours_from_now = difference.days * 24.0 + difference.seconds / (60.0 * 60.0)
    return hours_from_now

@json_response
@login_required
@has_card_query_filters
def next_card_due_at(request, deck=None, tags=None):
    '''Returns a human-readable format of the next date that the card is due.'''
    due_at = Card.objects.next_card_due_at(request.user, deck=deck, tags=tags)
    due_at = naturalday(due_at.date())
    return {'next_card_due_at': due_at}




@login_required
@json_response
@all_http_methods
def rest_card(request, card_id): #todo:refactor into facts (no???)
    if request.method == 'GET':
        card = get_object_or_404(Card, pk=card_id)

        #TODO refactor the below into a model - it's not DRY
        reviewed_at = datetime.datetime.utcnow()

        field_contents = \
            dict((field_content.field_type_id, field_content,) \
                 for field_content in card.fact.fieldcontent_set.all())
        card_context = {
                'card': card,
                'fields': field_contents,
                'fact': card.fact,
                'card_back_template': card.template.back_template_name,
        }

        due_times = {}
        for grade in [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,]:
            due_at = card._next_due_at(grade, reviewed_at, \
                card._next_interval(grade, \
                    card._next_ease_factor(grade, reviewed_at), \
                    reviewed_at))
            duration = due_at - reviewed_at
            days = duration.days + (duration.seconds / 86400.0)
            due_times[grade] = days

        formatted_card = {
            'id': card.id,
            'fact_id': card.fact_id,
            'front': render_to_string(\
                card.template.front_template_name, card_context),
            'back': render_to_string(\
                'flashcards/card_back.html', card_context),
            'next_due_at_per_grade': due_times,
        }

        return {'success': True, 'card': formatted_card}
        #return to_dojo_data(formatted_card)
    elif request.method == 'POST':
        if 'grade' in request.POST:
            # this is a card review
            #FIXME make sure this user owns this card
            card = get_object_or_404(Card, pk=card_id) 
            card.review(int(request.POST['grade']))
            return {'success': True}



# Undo stack for card reviews

@json_response
@login_required
def undo_review(request):
    if request.method == 'POST':
        UndoCardReview.objects.undo(request.user)
        return {'success': True}


@json_response
@login_required
def reset_review_undo_stack(request):
    if request.method == 'POST':
        UndoCardReview.objects.reset(request.user)
        return {'success': True}
