# Eventually this will supercede most of flashcards.views.api
# We're transitioning POX etc. RPC crap to mostly legit REST.

from apps.utils import japanese
from apps.utils.querycleaner import clean_query
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import forms
from django.forms.models import modelformset_factory, formset_factory
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.views.generic.create_update import (
        update_object, delete_object, create_object)
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from flashcards.forms import DeckForm, FactForm, FieldContentForm, CardForm
#from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
#from flashcards.models import FieldContent, Card
from flashcards import models
from flashcards.models import Card
from flashcards.models.undo import UndoCardReview
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL
from catnap.django_urls import absolute_reverse as reverse
from flashcards.views.decorators import has_card_query_filters
from apps.utils import querycleaner
from apps.utils.querycleaner import clean_query
import random
from flashcards.views.shortcuts import get_deck_or_404
from django.utils.decorators import method_decorator
from catnap.restviews import (JsonEmitterMixin, AutoContentTypeMixin,
        RestView, ListView, DetailView, DeletionMixin)
from flashcards.restresources import (
        UserResource, DeckResource, CardResource)
from catnap.exceptions import (HttpForbiddenException,
        HttpTemporaryRedirectException)
from catnap.auth import BasicAuthentication, DjangoContribAuthentication
from flashcards.contextprocessors import review_start_context


class ManabiRestView(JsonEmitterMixin, AutoContentTypeMixin, RestView):
    '''
    Our JSON-formatted response base class.
    '''
    content_type_template_string = 'application/vnd.org.manabi.{0}+json'

    authenticators = (DjangoContribAuthentication(),
                      BasicAuthentication(realm='manabi'))


class CardQueryFiltersMixin(object):
    def get_deck(self):
        if self.request.GET.get('deck'):
            return get_object_or_404(
                    models.Deck, pk=self.request.GET['deck'])

    def get_tags(self):
        try:
            #TODO support for multiple tags
            tag_id = int(self.request.GET.get('tags',
                    self.request.GET.get('tag', -1)))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            return usertagging.models.Tag.objects.filter(
                    id__in=tag_ids)




# Resource views

class EntryPoint(ManabiRestView):
    '''
    Entry-point to our REST API.
    This view's URL is the only one that clients should need to know,
    and the only one that should be documented in the API!

    Also includes some fields for reviewing all decks at once.
    '''
    def get(self, request):
        '''
        List the available top-level resource URLs.
        '''
        context = {
            'deck_list_url': reverse('rest-deck_list'),
            'shared_deck_list_url': reverse('rest-shared_deck_list'),
            'next_cards_for_review_url': reverse(
                    'rest-next_cards_for_review'),
            'review_undo_stack_url': reverse('rest-review_undo_stack'),
            'all_decks_url': reverse('rest-all_decks'),
        }
        return self.render_to_response(context)


class AllDecks(ManabiRestView):
    def get(self, request):
        context = review_start_context(self.request)
        context['owned_by_current_user'] = True
        return self.render_to_response(context)

    def get_url(self):
        return reverse('rest-all_decks')
    

class DeckList(ListView, ManabiRestView):
    '''
    List of the logged-in user's decks.
    '''
    content_subtype = 'DeckList'
    resource_class = DeckResource

    def get_queryset(self):
        return models.Deck.objects.filter(
            owner=self.request.user, active=True).order_by('name')

    def get_url(self):
        return reverse('rest-deck_list')
    
    
class Deck(DeletionMixin, DetailView, ManabiRestView):
    '''
    Detail view of a single deck.

    Could be the user's deck, or a shared one that he could add
    to his library.
    '''
    content_subtype = 'Deck'
    resource_class = DeckResource

    def get_object(self):
        deck = get_deck_or_404(self.request.user, self.kwargs.get('pk'))

        # If the user is already subscribed to this deck,
        # redirect to their subscribed copy.
        subscriber = deck.get_subscriber_deck_for_user(self.request.user)
        if subscriber:
            raise HttpTemporaryRedirectException(
                    reverse('rest-deck', args=[subscriber.id]))

        return deck

    def get_context_data(self, *args, **kwargs):
        '''
        Add `request.user`-dependent fields, for sharing or subscribing.
        '''
        context = super(Deck, self).get_context_data(*args, **kwargs)
        deck = self.get_object()

        context['owned_by_current_user'] = deck.owner == self.request.user

        # add the review-related data.
        if context['owned_by_current_user']:
            context.update(review_start_context(self.request, deck))
        else:
            context['subscription_url'] = reverse(
                    'rest-deck_subscription', args=[deck.id])


        return context
        

    def allowed_methods(self, request, *args, **kwargs):
        '''Don't return "DELETE" if the user has no permission.'''
        methods = super(Deck, self).allowed_methods(
                request, *args, **kwargs)
        deck = self.get_object()
        if deck.owner != request.user:
            methods.remove('delete')
        return methods
            



class SharedDeckList(ListView, ManabiRestView):
    '''
    List of shared decks from any user.
    '''
    content_subtype = 'DeckList'
    resource_class = DeckResource
    queryset = models.Deck.objects.shared_decks()

    def get_url(self):
        return reverse('rest-shared_deck_list')
     

class DeckSubscription(ManabiRestView):
    '''
    Currently a write-only resource, which is used to subscribe to
    another user's shared deck. Each shared deck has a DeckSubscription URL
    which can be POSTed to, with a response indicating the URL of the
    newly created deck in the user's library.

    If the user is already subscribed to the deck, it will return the URL
    of the already-subscribed deck copy.
    '''
    content_subtype = 'DeckSubscription'

    def post(self, request, **kwargs):
        user = self.request.user
        deck = get_deck_or_404(user, self.kwargs.get('pk'))

        # Is it already this user's deck?
        if deck.owner == user:
            return self.responses.see_other(
                    reverse('rest-deck', args=[deck.id]))
        
        # Check if the user is aready subscribed to this deck.
        subscriber_deck = deck.get_subscriber_deck_for_user(user)
        if subscriber_deck:
            return self.responses.see_other(
                    reverse('rest-deck', args=[subscriber_deck.id]))
                    

        # Create the new subscriber deck and give its URL.
        new_deck = deck.subscribe(user)
        return self.responses.created(
                reverse('rest-deck', args=[new_deck.id]))

        
class NextCardsForReview(CardQueryFiltersMixin, ManabiRestView):
    '''
    Returns a list of Card resources -- the next cards up for review.  
    Accepts some query parameters for filtering and influencing what
    cards will be selected.
    '''
    content_subtype = 'CardList'
    
    query_structure = {
        'count': int,
        'early_review': bool,
        'learn_more': bool,
        'session_start': bool, # Beginning of review session?
        'excluded_cards': querycleaner.int_list,
    }

    def get(self, request, **kwargs):
        params = clean_query(request.GET, self.query_structure)

        count = params.get('count', 5)

        next_cards = Card.objects.next_cards(
            request.user,
            count,
            excluded_ids=params.get('excluded_cards', []),
            session_start=params.get('session_start'),
            deck=self.get_deck(),
            tags=self.get_tags(),
            early_review=params.get('early_review'))

        #FIXME need to account for 0 cards returned 

        # Assemble a list of the cards to be serialized.
        return self.render_to_response({
            'card_list':
                [CardResource(card).get_data() for card in next_cards]
        })


class CardReviews(ManabiRestView):
    '''
    Currently a write-only resource for review operations.
    '''
    content_subtype = 'CardReview'
    
    def post(self, request, **kwargs):
        # `duration` is in seconds (the time taken from viewing the card 
        # to clicking Show Answer).
        params = clean_query(request.POST, {
            'grade': int,
            'duration': float,
            'questionDuration': float
        })

        card = get_object_or_404(Card, pk=self.kwargs.get('pk')) 

        if card.owner != request.user:
            raise PermissionDenied('You do not own this flashcard.')

        card.review(
            params['grade'],
            duration=params.get('duration'),
            question_duration=params.get('questionDuration'))

        return self.responses.no_content()




class ReviewUndo(ManabiRestView):
    '''
    Undo stack for card reviews.
    A write (POST) or delete-only resource, at the moment.
    '''
    def post(self, request):
        UndoCardReview.objects.undo(request.user)
        return self.responses.no_content()

    def delete(self, request):
        UndoCardReview.objects.reset(request.user)
        return self.responses.no_content()


