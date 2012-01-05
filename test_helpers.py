import random
import string

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.test import Client, TestCase
from django.utils import simplejson as json

from apps.flashcards.management.commands.flashcards_init import create_initial_data
from apps.flashcards.models import Deck, Card, Fact, FactType, FieldType, FieldContent

PASSWORD = 'whatever'

class ManabiTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        user = create_user()
        create_initial_data()

    def setUp(self):
        self.api = APIShortcuts(self)
        self.after_setUp()

    def after_setUp(self):
        pass

    def tearDown(self):
        self.before_tearDown()

    def before_tearDown(self):
        pass

    def _http_verb(self, verb, url, user=None, *args, **kwargs):
        '''
        Defaults to being logged-in with a newly created user.
        '''
        if user is None:
            user = create_user()
        self.client.login(username=user.username, password=PASSWORD)
        resp = getattr(self.client, verb)(url, user=user, *args, **kwargs)
        headers = dict(resp.items())
        if 'json' in headers.get('Content-Type', ''):
            resp.JSON = json.loads(resp.content)
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
        print response_or_url
        self.assertEqual(status_code, response_or_url.status_code)

    def assertApiSuccess(self, response):
        if isinstance(response, HttpResponse):
            response = json.loads(response.content)
        self.assertTrue(response.get('success'))
 
    def review_cards(self, user):
        ''' Returns the cards that were reviewed. '''
        ret = self.get(reverse('rest-next_cards_for_review'), user=user)
        cards = self.get(reverse('rest-next_cards_for_review'), user=user).JSON['card_list']
        import sys
        print >> sys.stderr, cards
        print >> sys.stderr, self.get(reverse('rest-deck_list'), user=user).JSON
        return cards
        #FIXME

class APIShortcuts(object):
    def __init__(self, test_case):
        self.tc = test_case

    def decks(self, user):
        return self.tc.get(reverse('rest-deck_list'), user=user).JSON['deck_list']

def random_name():
    return ''.join(random.choice(string.ascii_lowercase) for _ in xrange(6))

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
    return Deck.objects.create(
        name=random_name().title(),
        description='Example description',
        owner=owner,
    )

def create_fact(user=None, deck=None):
    """
    Includes card creation.
    """
    deck = deck or create_deck(user=user)
    fact = Fact.objects.create(
        deck=deck,
    )
    for template in FactType.objects.japanese.cardtemplate_set.all():
        card = Card(
            fact=fact,
            template=template,
        )
        card.randomize_new_order()
        card.save()
    for field_type in FactType.objects.japanese.fieldtype_set.all():
        FieldContent.objects.create(
            fact=fact,
            field_type=field_type,
            content=random_name(),
        )
    return fact

