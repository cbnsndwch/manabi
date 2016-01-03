from rest_framework import serializers

from manabi.api.serializers import ManabiModelSerializer
from manabi.apps.flashcards.models import Deck, Fact, Card
from manabi.apps.manabi_auth.serializers import UserSerializer


class DeckSerializer(ManabiModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Deck
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'card_count',
            'shared',
            'shared_at',
            'created_at',
            'modified_at',
            'suspended',
        )


class FactSerializer(ManabiModelSerializer):
    card_count = serializers.ReadOnlyField()

    def to_representation(self, obj):
        data = super(FactSerializer, self).to_representation(obj)

        if obj.pulls_from_upstream:
            data.update({
                'expression': obj.synchronized_with.expression,
                'reading': obj.synchronized_with.reading,
                'meaning': obj.synchronized_with.meaning,
            })

        return data

    class Meta:
        model = Fact
        fields = (
            'id',
            'deck',
            'active',
            'expression',
            'card_count',
            'reading',
            'meaning',
            'created_at',
            'modified_at',
        )


class CardSerializer(ManabiModelSerializer):
    expression = serializers.CharField(source='fact.expression')
    reading = serializers.CharField(source='fact.reading')
    meaning = serializers.CharField(source='fact.meaning')

    class Meta:
        model = Card
        fields = (
            'id',
            'deck',
            'fact',
            'ease_factor',
            'interval',
            'due_at',
            'last_ease_factor',
            'last_interval',
            'last_due_at',
            'review_count',
            'template',
            'expression',
            'reading',
            'meaning',
        )
