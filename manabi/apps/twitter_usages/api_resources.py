from catnap.rest_resources import RestModelResource
from django.core.urlresolvers import reverse


class TweetResource(RestModelResource):
    fields =[
        'id',
        'tweet',
    ]
