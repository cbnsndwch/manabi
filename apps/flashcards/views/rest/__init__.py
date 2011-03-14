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
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL

from catnap.django_urls import absolute_reverse as reverse
from flashcards.views.decorators import has_card_query_filters
import apps.utils.querycleaner
import random
from flashcards.views.shortcuts import get_deck_or_404
from django.utils.decorators import method_decorator
from catnap.restviews import (JsonEmitterMixin, AutoContentTypeMixin,
        RestView, ListView, DetailView, DeletionMixin)
from flashcards.restresources import UserResource, DeckResource
from catnap.exceptions import HttpForbiddenException
from catnap.auth import BasicAuthentication


class ManabiRestView(JsonEmitterMixin, AutoContentTypeMixin, RestView):
    '''
    Our JSON-formatted response base class.
    '''
    content_type_template_string = 'application/vnd.org.manabi.{0}+json'

    authenticator = BasicAuthentication(realm='manabi')

    ##@method_decorator(login_required)
    #def dispatch(self, *args, **kwargs):
    #    return super(ManabiRestView, self).dispatch(*args, **kwargs)



# Resource views

class EntryPoint(ManabiRestView):
    '''
    Entry-point to our REST API.
    This view's URL is the only one that clients should need to know,
    and the only one that should be documented in the API!
    '''
    def get(self, request):
        '''
        List the available top-level resource URLs.
        '''
        context = {
            'deck_list_url': reverse('rest-deck_list'),
            'shared_deck_list_url': reverse('rest-shared_deck_list'),
            #'users': reverse('rest-users'),
        }
        return self.render_to_response(context)


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
        return deck

    def get_context_data(self, *args, **kwargs):
        '''
        Add `request.user`-dependent fields, for sharing or subscribing.
        '''
        context = super(Deck, self).get_context_data(*args, **kwargs)
        deck = self.get_object()

        context['owned_by_current_user'] = deck.owner == self.request.user
        context['card_count'] = deck.card_count

        if deck.owner != self.request.user:
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

        



