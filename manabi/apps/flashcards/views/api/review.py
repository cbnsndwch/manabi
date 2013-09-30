import datetime
import string
import subprocess

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

from apps.utils import querycleaner
from apps.utils.querycleaner import clean_query
from flashcards.models import Card
from flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY)
from flashcards.models.undo import UndoCardReview
from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import has_card_query_filters



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
def due_card_count(request):
    user = request.user
    return Card.objects.common_filters(user).due(user).count()

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

