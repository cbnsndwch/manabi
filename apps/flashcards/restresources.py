from catnap.restresources import RestResource, RestModelResource
from django.core.urlresolvers import reverse


class UserResource(RestModelResource):
    fields = ('id', 'username', 'first_name', 'last_name', 'date_joined',)

    #def get_data(self):
        #data = super(UserResource, self).get_data()



class DeckResource(RestModelResource):
    fields = ('name', 'description', 'owner',
              'shared', 'shared_at', 'created_at', 'modified_at',)

    def get_url_path(self):
        return reverse('rest-deck', args=[self.obj.id])

    def get_data(self):
        data = super(DeckResource, self).get_data()
        data['owner'] = UserResource(self.obj.owner).get_data()
        #data['request_user_is_owner'] = 
        return data





