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
    def __init__(
        self,
        user,
        deck=None,
        excluded_card_ids=set(),
        time_zone=None,
    ):
        self.user = user
        self.time_zone = time_zone
        self.deck = deck
        self.excluded_card_ids = excluded_card_ids

    @property
    def _base_cards_queryset(self):
        cards = Card.objects.available()

        if self.deck:
            cards = cards.of_deck(self.deck)

        if self.excluded_card_ids:
            cards = cards.excluding_ids(self.excluded_card_ids)

        return cards

    @property
    @lru_cache(maxsize=None)
    def ready_for_review(self):
        if self.user.is_anonymous():
            return False

        return self._base_cards_queryset.due(self.user).exists()

    @lru_cache(maxsize=None)
    def _reviewed_today_count(self):
        return CardHistory.objects.of_day(
            self.user, self.time_zone).count()

    @property
    @lru_cache(maxsize=None)
    def next_new_cards_count(self):
        if self.user.is_anonymous():
            return 0

        new_card_count = self._base_cards_queryset.new_count(self.user)

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

        return self._base_cards_queryset.filter(
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
