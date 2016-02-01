from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from manabi.api.viewsets import MultiSerializerViewSetMixin
from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
)
from manabi.apps.flashcards.serializers import (
    DeckSerializer,
    FactSerializer,
    FactWithCardsSerializer,
    DetailedFactSerializer,
    CardSerializer,
)


class DeckViewSet(viewsets.ModelViewSet):
    serializer_class = DeckSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated():
            return Deck.objects.none()
        return Deck.objects.filter(owner=user, active=True).order_by('name')

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()

    @detail_route()
    def cards(self, request, pk=None):
        deck = self.get_object()
        cards = Card.objects.of_deck(deck, with_upstream=True)
        return Response(CardSerializer(cards, many=True).data)

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        facts = Fact.objects.deck_facts(deck)
        facts = facts.select_related('deck')
        facts = facts.prefetch_related('card_set')
        return Response(DetailedFactSerializer(facts, many=True).data)


class SharedDeckViewSet(viewsets.ModelViewSet):
    serializer_class = DeckSerializer

    @detail_route()
    def facts(self, request, pk=None):
        deck = self.get_object()
        facts = Fact.objects.deck_facts(deck)
        return Response(FactSerializer(facts, many=True).data)

    def get_queryset(self):
        decks = Deck.objects.filter(active=True, shared=True)

        if self.request.user.is_authenticated():
            decks = decks.exclude(owner=self.request.user)

        return decks.order_by('name')


class FactViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    serializer_class = DetailedFactSerializer
    serializer_action_classes = {
        'create': FactWithCardsSerializer,
        'update': FactWithCardsSerializer,
    }
    permissions_classes = [IsAuthenticated]

    def get_queryset(self):
        facts = Fact.objects.with_upstream(user=self.request.user)
        facts = facts.filter(active=True).distinct()
        facts = facts.select_related('deck')
        facts = facts.prefetch_related('card_set')
        return facts

    # TODO Special code for getting a specific object, for speed.


class NextCardForReviewViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        count = 5
        next_cards = Card.objects.next_cards(
            self.request.user,
            count,
            #TODO
        )
        # FIXME Properly support this endpoint, incl filtering.
        return Card.objects.filter(pk__in=[card.pk for card in next_cards])
