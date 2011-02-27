from apps.utils import querycleaner
from apps.utils.querycleaner import clean_query
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import forms
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.template.loader import render_to_string
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from flashcards.models import Card
from flashcards.models.constants import GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY
from flashcards.models.undo import UndoCardReview
from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import has_card_query_filters
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
    '''
    This is the one HTML view which is part of the API (so far).
    It renders the subfacts for a given fact.
    '''
    parent_fact = get_object_or_404(Fact, pk=parent_fact_id)
    context = {'subfacts': parent_fact.subfacts.all()}
    return render_to_response('flashcards/subfacts.html', context)


@api
@has_card_query_filters
def next_cards_for_review(request, deck=None, tags=None):
    query_structure = {
        'count': int,
        'early_review': bool,
        'learn_more': bool,
        'session_start': bool, # Beginning of review session?
        'excluded_cards': querycleaner.int_list,
    }

    if request.method == 'GET':
        params = clean_query(request.GET, query_structure)

        count = params.get('count', 5)

        # New cards per day limit.
        #TODO implement this to be user-configurable instead of hard-coded
        #daily_new_card_limit = NEW_CARDS_PER_DAY

        # Learn More new cards. Usually this will be 
        # combined with early_review.
        #if params.get('learn_more'):
            # Overrides the daily new card limit
            #daily_new_card_limit = None

        next_cards = Card.objects.next_cards(
            request.user,
            count,
            excluded_ids=params.get('excluded_cards', []),
            session_start=params.get('session_start'),
            deck=deck,
            tags=tags,
            early_review=params.get('early_review'))
            #daily_new_card_limit=daily_new_card_limit)

        #FIXME need to account for 0 cards returned 

        # Format into JSON object.
        formatted_cards = []
        for card in next_cards:
            formatted_cards.append(card.to_api_dict())

        return formatted_cards

@api
def due_card_count(request):
    return Card.objects.common_filters(request.user).due().count()

@api
def new_card_count(request):
    return Card.objects.common_filters(request.user).new().count()

@api
@has_card_query_filters
def due_tomorrow_count(request, deck=None, tags=None):
    return Card.objects.count_of_cards_due_tomorrow(
        request.user, deck=deck, tags=tags)

@api
@has_card_query_filters
def hours_until_next_card_due(request, deck=None, tags=None):
    cards = Card.objects.common_filters(request.user,
        deck=deck, tags=tags)
    due_at = cards.next_card_due_at()
    difference = due_at - datetime.datetime.utcnow()
    hours_from_now = (difference.days * 24.0
                      + difference.seconds / (60.0 * 60.0))
    return hours_from_now

@api
@has_card_query_filters
def next_card_due_at(request, deck=None, tags=None):
    '''
    Returns a human-readable format of the next date that the card is due.
    '''
    cards = Card.objects.common_filters(request.user,
        deck=deck, tags=tags)
    due_at = cards.next_card_due_at()
    return naturalday(due_at.date())


@api
def rest_card(request, card_id): 
    '''
    Used for retrieving a specific card for reviewing it,
    or for submitting the grade of a card that has just been reviewed.
    '''
    #TODO refactor into facts (or no???)
    if request.method == 'GET':
        card = get_object_or_404(Card, pk=card_id)
        return card.to_api_dict()
    elif request.method == 'POST':
        # `duration` is in seconds (the time taken from viewing the card 
        # to clicking Show Answer).
        params = clean_query(request.POST,
            {'grade': int, 'duration': float, 'questionDuration': float})

        if 'grade' in request.POST:
            # This is a card review.
            #
            card = get_object_or_404(Card, pk=card_id) 

            if card.owner != request.user:
                raise PermissionDenied('You do not own this flashcard.')

            card.review(params['grade'],
                duration=params.get('duration'),
                question_duration=params.get('questionDuration'))

            return {'success': True}



# Undo stack for card reviews

@api
def undo_review(request):
    if request.method == 'POST':
        UndoCardReview.objects.undo(request.user)
        return {'success': True}


@api
def reset_review_undo_stack(request):
    if request.method == 'POST':
        UndoCardReview.objects.reset(request.user)
        return {'success': True}



