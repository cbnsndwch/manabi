import random
import string

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, TestCase
from django.utils import simplejson as json


class ManabiTestCase(TestCase):
    def setUp(self):
        pass

    def _http_verb(verb, user=None, *args, **kwargs):
        '''
        Defaults to being logged-in with a newly created user.
        '''
        if user is None:
            user = create_user()
        self.client.get(*args, user=user, **kwargs)

    def get(*args, **kwargs):
        return self._http_verb('get', *args, **kwargs)

    def post(*args, **kwargs):
        return self._http_verb('post', *args, **kwargs)

    def assertStatus(status_code, response_or_url):
        if isinstance(response_or_url, basestring):
            response_or_url = self.get(response_or_url)
        self.assertEqual(status_code, response_or_url.status_code)

    def assertApiSuccess(response):
        if isinstance(response, HttpResponse):
            response = json.loads(response.content)
        self.assertTrue(response.get('success'))


def create_user():
    username = ''.join(random.choice(string.ascii_lowercase) for _ in xrange(6))
    return User.objects.create_user(username, 'foo@example.com', 'password')

def create_staff():
    user = create_user()
    user.is_staff = True
    user.save()

