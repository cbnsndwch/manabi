from catnap.restresources import RestResource, RestModelResource
from django.core.urlresolvers import reverse



class UserResource(RestModelResource):
    fields = ('id', 'username', 'first_name', 'last_name', 'date_joined',)

    def get_data(self):
        data = super(UserResource, self).get_data()
        data['full_name'] = self.obj.get_full_name()
        return data



class DeckResource(RestModelResource):
    fields = ('id', 'name', 'description', 'owner',
              'shared', 'shared_at', 'created_at', 'modified_at',)

    def get_url_path(self):
        return reverse('rest-deck', args=[self.obj.id])

    def get_data(self):
        data = super(DeckResource, self).get_data()
        data['owner'] = UserResource(self.obj.owner).get_data()
        data['card_count'] = self.obj.card_count

        return data

class CardReviewsResource(RestResource):
    def __init__(self, card):
        self.card = card

    def get_url_path(self):
        return reverse('rest-card_reviews', args=[self.card.obj.id])

class CardResource(RestModelResource):
    fields = ('id', 'fact_id', 'ease_factor', 'interval', 'due_at',
              'last_ease_factor', 'last_interval', 'last_due_at',
              'review_count')

    #def get_url_path(self):
    #    return reverse('rest-card', args=[self.obj.id])
    
    def get_data(self):
        data = super(CardResource, self).get_data()
        data.update({
            'front': self.obj.render_front(),
            'back': self.obj.render_back(),
            'next_due_at_per_grade':
                dict((grade, rep.due_at)
                     for (grade, rep)
                     in self.obj.next_repetition_per_grade().items()),

            'reviews_url': CardReviewsResource(self).get_url()
        })
        return data

