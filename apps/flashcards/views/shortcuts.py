from catnap.exceptions import HttpForbiddenException
from django.forms import forms
from django.shortcuts import get_object_or_404

from flashcards.forms import DeckForm, FactForm, FieldContentForm, CardForm
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
from flashcards.models import FieldContent, Card
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL


def get_deck_or_404(user, pk, must_own=False):
    '''
    Returns the deck with the given pk. 404s, or raises an exception
    if the user doesn't own that deck and it's not shared.
    '''
    deck = get_object_or_404(Deck, pk=pk)

    # The user must either own it, or it must be a shared deck.
    if deck.owner != user and (must_own or not deck.shared):
        msg = 'You do not have permission to access this deck.'
        if not must_own:
            msg += ' This deck is not shared.'
        raise HttpForbiddenException(msg)

    return deck

