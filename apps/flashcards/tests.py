# -*- coding: utf-8 -*-
import urllib

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User

import settings
from manabi.apps.flashcards.models import Deck
from manabi.test_helpers import ManabiTestCase, create_sample_data, create_user


class TestAPI(ManabiTestCase):
    def after_setUp(self):
        self.user = create_user()

    def test_deck_list(self):
        create_sample_data(facts=30, user=self.user)
        self.assertEqual(1, Deck.objects.filter(owner=self.user).count())
        decks = self.api.decks(self.user)
        self.assertEqual(1, len(decks))

