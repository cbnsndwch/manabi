from catnap.restviews import (JsonEmitterMixin, AutoContentTypeMixin,
                              RestView, ListView, DetailView, DeletionMixin)
from catnap.auth import BasicAuthentication, DjangoContribAuthentication
from manabi.apps.utils import japanese, query_cleaner
from manabi.apps.utils.query_cleaner import clean_query
from manabi.apps.flashcards.models import Card
from manabi.apps.flashcards.models.undo import UndoCardReview
from manabi.apps.flashcards.restresources import UserResource, DeckResource, CardResource
from manabi.apps.flashcards import models
from manabi.apps.utils.shortcuts import get_deck_or_404


class ManabiRestView(JsonEmitterMixin, AutoContentTypeMixin, RestView):
    '''
    Our JSON-formatted response base class.
    '''
    content_type_template_string = 'application/vnd.org.manabi.{0}+json'

    authenticators = (DjangoContribAuthentication(),
                      BasicAuthentication(realm='manabi'))


class CardQueryMixin(object):
    def get_deck(self):
        if self.request.GET.get('deck'):
            return get_object_or_404(
                    models.Deck, pk=self.request.GET['deck'])


class NextCardsForReview(CardQueryMixin, ManabiRestView):
    '''
    Returns a list of Card resources -- the next cards up for review.  
    Accepts some query parameters for filtering and influencing what
    cards will be selected.
    '''
    query_structure = {
        'count': int,
        'early_review': bool,
        'learn_more': bool,
        'session_start': bool, # Beginning of review session?
        'excluded_cards': query_cleaner.int_list,
    }

    def get(self, request, **kwargs):
        params = clean_query(request.GET, self.query_structure)

        count = params.get('count', 5)

        next_cards = models.Card.objects.next_cards(
            request.user,
            count,
            excluded_ids=params.get('excluded_cards', []),
            session_start=params.get('session_start'),
            deck=self.get_deck(),
            early_review=params.get('early_review'),
            learn_more=params.get('learn_more'),
        )

        #FIXME need to account for 0 cards returned 

        # Assemble a list of the cards to be serialized.
        return self.render_to_response({
            'card_list':
                [CardResource(card).get_data() for card in next_cards],
        })

