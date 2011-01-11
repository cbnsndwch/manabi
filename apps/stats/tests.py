# -*- coding: utf-8 -*-

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User
import urllib
import settings


class StatsTest(TestCase):
    fixtures = ['sample_db.json']

    def setUp(self):
        pass

    def do_login(self):
        self.login = self.client.login(
            username='alex', password='w')
        self.failUnless(self.login, 'Could not log in')

    def tearDown(self):
        pass
        
    def test_reps_view(self):
        self.do_login()

        res = self.client.get(reverse('graphs_repetitions'))

        self.assertEqual(res.status_code, 200)

        json = simplejson.loads(res.content)

        self.assertTrue(json['success'])
        self.assertTrue('series' in json['data'])
        


