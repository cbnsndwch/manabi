from flashcards.forms import DeckForm, FactForm, FieldContentForm, CardForm
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
from flashcards.models import FieldContent, Card
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL
from django.forms import forms

from django.shortcuts import get_object_or_404


def get_deck_or_404(user, pk):
    '''
    Returns the deck with the given pk. 404s, or raises an exception
    if the user doesn't own that deck and it's not shared.
    '''
    deck = get_object_or_404(Deck, pk=pk)

    # The user must either own it, or it must be a shared deck.
    if deck.owner != user and not deck.shared:
        raise HttpForbiddenException(
                'You do not have permission to view this deck. '
                'This deck is not shared.')
    #if deck.owner_id != user.id:
    #    #TODO should be a permissions error instead
    #    raise forms.ValidationError(
    #        'You do not have permission to access this flashcard deck.')
    return deck



