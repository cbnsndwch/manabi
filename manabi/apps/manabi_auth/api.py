from collections import defaultdict

from django.http import HttpResponseBadRequest


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
        
