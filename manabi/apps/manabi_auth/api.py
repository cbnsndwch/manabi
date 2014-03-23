from collections import defaultdict

from django.http import HttpResponseBadRequest

from manabi.apps.manabi_auth.rest_resources import UserResource
from manabi.rest import ManabiRestView


class AuthenticationStatus(ManabiRestView):
    '''
    Returns whether the user is authenticated.
    '''
    def get(self, request, **kwargs):
        return self.render_to_response({
            'is_authenticated': request.user.is_authenticated(),
        })


class User(ManabiRestView):
    '''
    Used for signup.
    '''
    resource_class = UserResource

    def post(self, request, **kwargs):
        if kwargs.get('user'):
            return HttpResponseBadRequest()

        params = clean_query(request.POST, {
            'username': unicode,
            'email': unicode,
            'password': unicode,
        })

        errors = defaultdict()

        #if not 
        
