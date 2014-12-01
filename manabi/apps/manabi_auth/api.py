from collections import defaultdict

from catnap.rest_forms import ModelFormViewMixin
from django.http import HttpResponseBadRequest

from manabi.apps.utils import query_cleaner
from manabi.apps.manabi_auth.rest_resources import UserResource
from manabi.apps.manabi_auth.forms import UserCreationForm
from manabi.rest import ManabiRestView


class AuthenticationStatus(ManabiRestView):
    '''
    Returns whether the user is authenticated.
    '''
    def get(self, request, **kwargs):
        return self.render_to_response({
            'is_authenticated': request.user.is_authenticated(),
        })


class User(ModelFormViewMixin, ManabiRestView):
    '''
    Used for signup.
    '''
    resource_class = UserResource
    form_class = UserCreationForm
