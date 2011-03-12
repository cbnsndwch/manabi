from flashcards.forms import DeckForm, FactForm, FieldContentForm, CardForm
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
from flashcards.models import FieldContent, Card
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL
from django.forms import forms

from django.shortcuts import get_object_or_404


def get_deck_or_404(user, pk):
    '''
    Returns the deck with the given pk. 404s, or raises an exception
    if the user doesn't own that deck.
    '''
    deck = get_object_or_404(Deck, pk=pk)
    if deck.owner_id != user.id:
        #TODO should be a permissions error instead
        raise forms.ValidationError(
            'You do not have permission to access this flashcard deck.')
    return deck



