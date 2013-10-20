import random
import string
import sys
from django.conf import settings

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.test import Client, TestCase
from django.utils import simplejson as json

from manabi.apps.flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY)
from manabi.apps.flashcards.models import (Deck, Card, Fact, FactType, FieldType,
                                           FieldContent, CardTemplate)
from manabi.apps.flashcards.models.cards import CARD_TEMPLATE_CHOICES


PASSWORD = 'whatever'


class ManabiTestCase(TestCase):
    longMessage = True

    @classmethod
    def setUpClass(cls):
        user = create_user()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.api = APIShortcuts(self)
        settings.DEFAULT_URL_PREFIX = 'http://testserver'

        self.after_setUp()

    def after_setUp(self):
        pass

    def tearDown(self):
        self.before_tearDown()

    def before_tearDown(self):
        pass

    def _http_verb(self, verb, url, *args, **kwargs):
        ''' Defaults to being logged-in with a newly created user. '''
        user = kwargs.pop('user')
        if user is None:
            user = create_user()
        self.client.login(username=user.username, password=PASSWORD)
        resp = getattr(self.client, verb)(url, user=user, *args, **kwargs)
        headers = dict(resp.items())
        if 'json' in headers.get('Content-Type', ''):
            resp.json = json.loads(resp.content)
        return resp

    def get(self, *args, **kwargs):
        return self._http_verb('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._http_verb('post', *args, **kwargs)

    #def _api_verb(self, verb, url, user=None, *args, **kwargs):
    #    if user is None:
    #        user = create_user()
    #    getattr(self.client, verb)
    #def api_get(self, *args, **kwargs):
    #        user_pass = base64.b64decode(data)

    def assertStatus(self, status_code, response_or_url):
        if isinstance(response_or_url, basestring):
            response_or_url = self.get(response_or_url)
        self.assertEqual(status_code, response_or_url.status_code)

    def assertApiSuccess(self, response):
        if isinstance(response, HttpResponse):
            response = json.loads(response.content)
        self.assertTrue(response.get('success'))
 
    def review_cards(self, user):
        ''' Returns the cards that were reviewed. '''
        cards = self.api.next_cards_for_review(user)
        for card in cards:
            self.api.review_card(self.user, card, GRADE_GOOD)
        return cards


class APIShortcuts(object):
    def __init__(self, test_case):
        self.tc = test_case

    def call(self, *args, **kwargs):
        method = kwargs.get('method')
        user = kwargs.get('user')
        ret = getattr(self.tc, method)(*args, user=user)
        #self.tc.assertTrue(200 <= ret.status_code < 300, msg=ret.content)
        self.tc.assertTrue(200 <= ret.status_code < 300,
                           msg='{}\n{}\n{}'.format(ret.status_code, args[0], ret.content))
        return ret

    def get(self, *args, **kwargs):
        kwargs['method'] = 'get'
        return self.call(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs['method'] = 'post'
        return self.call(*args, **kwargs)

    def decks(self, user):
        resp = self.get('/api/decks/', user=user)
        print resp.json
        return resp.json['decks']

    def next_cards_for_review(self, user):
        return self.get('/api/next_cards_for_review/', user=user).json['cards']

    def review_card(self, user, card, grade):
        return self.post(card['reviews_url'], {'grade': grade}, user=user)


def random_name():
    return ''.join(random.choice(string.ascii_lowercase) for _ in xrange(5))

def create_user():
    username = random_name()
    return User.objects.create_user(username, 'foo@example.com', PASSWORD)

def create_staff():
    user = create_user()
    user.is_staff = True
    user.save()
    return user


# Data creation.

def create_sample_data(user=None, facts=100):
    deck = create_deck(user=user)
    return [create_fact(user=user, deck=deck) for _ in xrange(facts)]

def create_deck(user=None):
    owner = user or create_user()
    deck = Deck.objects.create(
        name=random_name().title(),
        description='Example description',
        owner=owner,
    )
    return deck

def create_fact(user=None, deck=None):
    """ Includes card creation. """
    deck = deck or create_deck(user=user)
    fact = Fact.objects.create(
        deck=deck,
        expression=random_name(),
        reading=random_name(),
        meaning=random_name(),
    )

    for template, template_name in CARD_TEMPLATE_CHOICES:
        card = Card(
            deck=deck,
            fact=fact,
            template=template,
        )
        card.randomize_new_order()
        card.save()

    return fact

