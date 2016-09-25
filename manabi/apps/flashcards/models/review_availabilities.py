# -*- coding: utf-8 -*-

from datetime import datetime

from django.utils.lru_cache import lru_cache

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
    @lru_cache(maxsize=None)
    def ready_for_review(self):
        if self.user.is_anonymous():
            return False

        cards = Card.objects.all()
        if self.deck:
            cards = cards.of_deck(self.deck)

        return cards.due(self.user).exists()

    @lru_cache(maxsize=None)
    def _reviewed_today_count(self):
        return CardHistory.objects.of_day(
            self.user, self.time_zone).count()

    @property
    @lru_cache(maxsize=None)
    def next_new_cards_count(self):
        if self.user.is_anonymous():
            return 0

        cards = Card.objects.available()
        if self.deck is None:
            cards = cards.of_deck(self.deck)
        new_card_count = cards.new_count(self.user)

        remaining = max(
            0, min(
                new_card_count,
                NEW_CARDS_PER_DAY_LIMIT - self._reviewed_today_count()
            ),
        )
        return remaining

    @property
    @lru_cache(maxsize=None)
    def new_cards_per_day_limit_reached(self):
        return NEW_CARDS_PER_DAY_LIMIT - self._reviewed_today_count() <= 0

    @property
    @lru_cache(maxsize=None)
    def new_cards_per_day_limit_override(self):
        '''
        If the user wants to continue learning new cards beyond the daily
        limit, this value provides the overridden daily limit to use (based
        off `next_new_cards_count`).
        '''
        if not self.new_cards_per_day_limit_reached:
            return None
        return self._reviewed_today_count() + self.next_new_cards_count

    @property
    @lru_cache(maxsize=None)
    def early_review_available(self):
        if self.user.is_anonymous():
            return False

        return Card.objects.of_user(self.user).available().filter(
            due_at__gt=datetime.utcnow()
        ).exists()

    @lru_cache(maxsize=None)
    def _prompts(self):
        if self.user.is_anonymous():
            return (
                u"",
                u"",
            )

        return (
            u"This text will tell you about the cards ready for you to learn or review.",
            u"I haven't built this part of the backend API yet—this is beta, it'll come before release!"
        )

    @property
    def primary_prompt(self):
        return self._prompts()[0]

    @property
    def secondary_prompt(self):
        return self._prompts()[1]
