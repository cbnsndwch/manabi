from django.views.decorators.cache import cache_page
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve
from django.db.models import F
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from flashcards.models import (FactType, Fact, Deck, CardTemplate,
    FieldType, FieldContent, Card,
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY)
from flashcards.contextprocessors import subfact_form_context
from flashcards.contextprocessors import (
    deck_count_context, card_existence_context, fact_add_form_context)
from flashcards.forms import DeckForm, FactForm, FieldContentForm
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
from flashcards.models import FieldContent, Card
from flashcards.views.shortcuts import get_deck_or_404


LOGIN_URL = '/popups/login/'

@login_required(login_url=LOGIN_URL)
def deck_chooser(request):
    '''Create a deck, or choose a deck to add cards to.'''
    context = {
        'deck_list': Deck.objects.of_user(request.user),
    }
    return render_to_response('popups/deck_chooser.html', context,
                              context_instance=RequestContext(request))

@login_required(login_url=LOGIN_URL)
def fact_add_form(request, deck_id=None):
    '''Form for creating facts.'''
    deck = get_deck_or_404(request.user, deck_id)

    context = fact_add_form_context(request, deck=deck,
                                    autofocus=True, popup_window=True,
                                    takes_initial_values_from_GET=True)

    return render_to_response('popups/fact_add_form.html', context,
                              context_instance=RequestContext(request))

