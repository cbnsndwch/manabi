from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from manabi.apps.flashcards.models import (
    Deck,
)


def _get_bool(request, field_name):
    value = request.query_params.get(field_name, 'false').lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise ValidationError(
            "Invalid {} value.".format(field_name))


def review_filters(request):
    deck = None
    deck_id = request.query_params.get('deck_id')
    if deck_id:
        deck = get_object_or_404(Deck, pk=deck_id)

    early_review = _get_bool(request, 'early_review')

    return {
        'deck': deck,
        'early_review': early_review,
    }
