from catnap.rest_resources import RestResource, RestModelResource
from django.core.urlresolvers import reverse


class UserResource(RestModelResource):
    fields = ['id', 'username', 'first_name', 'last_name', 'date_joined']

    def get_data(self):
        data = super(UserResource, self).get_data()
        data['full_name'] = self.obj.get_full_name()
        return data

