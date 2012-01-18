# -*- coding: utf-8 -*-
import urllib

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User

import settings
from manabi.test_helpers import ManabiTestCase, create_sample_data, create_user


class StatsTest(ManabiTestCase):
    def setUp(self):
        self.user = create_user()
        create_sample_data(facts=30, user=self.user)
        self.review_cards(self.user)

    def test_reps_view(self):
        res = self.get(reverse('graphs_repetitions'), user=self.user)
        self.assertStatus(200, res)

        self.assertApiSuccess(res)
        self.assertTrue('series' in res.JSON['data'])
        from manabi.apps.flashcards.models import CardHistory
        user_items = CardHistory.objects.of_user(self.user)
        import sys
        print >> sys.stderr, user_items
        self.assertTrue(any([series['data'] for series in res.JSON['data']['series']]))
        
    def test_due_counts_view(self):
        res = self.get(reverse('graphs_due_counts'), user=self.user)
        self.assertStatus(200, res)

        self.assertApiSuccess(res)
        json = simplejson.loads(res.content)
        self.assertTrue('series' in json['data'])

