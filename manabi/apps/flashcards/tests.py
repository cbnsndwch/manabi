# -*- coding: utf-8 -*-

import json
import urllib

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings

from manabi.apps.flashcards.models import Deck
from manabi.apps.flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY)
from manabi.test_helpers import ManabiTestCase, create_sample_data, create_user


class DecksAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=1, user=self.user)

    def test_deck_list(self):
        self.assertEqual(1, Deck.objects.filter(owner=self.user).count())
        decks = self.api.decks(self.user)
        self.assertEqual(1, len(decks))


class ReviewsAPITest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=30, user=self.user)

    def test_next_cards_for_review(self):
        self.assertTrue(self.api.next_cards_for_review(self.user))

    def test_review_cards(self):
        count = 0
        while True:
            cards = self.review_cards(self.user)
            if not cards:
                break
            count += 1
            card_ids = map(lambda card: card['id'], cards)

            next_cards = self.api.next_cards_for_review(self.user)['cards']
            for card in next_cards:
                self.assertFalse(card['id'] in card_ids)
        self.assertTrue(count)

    def test_review_availabilities(self):
        pass


class SynchronizationTest(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()
        create_sample_data(facts=30, user=self.user)

        self.shared_deck = Deck.objects.filter(owner=self.user).first()
        self.shared_deck.share()

        self.subscriber = create_user()

    def test_deck_subscription(self):
        self.api.add_shared_deck(self.shared_deck, self.subscriber)
        shared_deck = Deck.objects.get(owner=self.subscriber)
        self.assertEqual(
            shared_deck.synchronized_with_id,
            self.shared_deck.id,
        )
