from datetime import datetime

from manabi.apps.flashcards.models.constants import (
    NEW_CARDS_PER_DAY_LIMIT,
)
from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
    CardHistory,
)


class ReviewAvailabilities(object):
    def __init__(self, user, deck=None, time_zone=None):
        self.user = user
        self.time_zone = time_zone
        self.deck = deck

    @property
    def ready_for_review(self):
        cards = Card.objects.all()
        if self.deck:
            cards = cards.of_deck(self.deck)

        return cards.due(self.user).exists()

    @property
    def next_new_cards_count(self):
        reviewed_today = CardHistory.objects.of_day(
            self.user, self.time_zone).count()

        cards = Card.objects.available()
        if self.deck is None:
            cards = cards.of_deck(self.deck)
        new_card_count = cards.new_count(self.user)

        remaining = max(
            0, min(new_card_count, NEW_CARDS_PER_DAY_LIMIT - reviewed_today),
        )
        return remaining

    @property
    def early_review_available(self):
        return Card.objects.of_user(self.user).available().filter(
            due_at__gt=datetime.utcnow()
        ).exists()

    def _prompts(self):
        return ('Primary', 'Secondary')

    @property
    def primary_prompt(self):
        return self._prompts()[0]

    @property
    def secondary_prompt(self):
        return self._prompts()[1]
