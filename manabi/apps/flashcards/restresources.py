from catnap.rest_resources import RestResource, RestModelResource
from django.core.urlresolvers import reverse


class UserResource(RestModelResource):
    fields = ['id', 'username', 'first_name', 'last_name', 'date_joined']

    def get_data(self):
        data = super(UserResource, self).get_data()
        data['full_name'] = self.obj.get_full_name()
        return data


class DeckResource(RestModelResource):
    fields = [
        'id',
        'name',
        'description',
        'owner',
        'shared',
        'shared_at',
        'created_at',
        'modified_at',
    ]

    def get_url_path(self):
        return ''#TODO reverse('rest-deck', args=[self.obj.id])

    def get_data(self):
        data = super(DeckResource, self).get_data()
        data.update({
            'owner': UserResource(self.obj.owner).get_data(),
            'card_count': self.obj.card_count(),
            'status_url': '',#TODO reverse('rest-deck_status', args=[self.obj.id]),
        })
        return data


class CardReviewsResource(RestResource):
    def __init__(self, card):
        self.card = card

    def get_url_path(self):
        return reverse('api_card_review', args=[self.card.obj.id])


class CardResource(RestModelResource):
    fields = [
        'id',
        'fact_id',
        'ease_factor',
        'interval',
        'due_at',
        'last_ease_factor',
        'last_interval',
        'last_due_at',
        'review_count',
    ]

    def get_url_path(self):
        return reverse('api_card', args=[self.obj.id])

    def get_data(self):
        data = super(CardResource, self).get_data()

        data.update({
            'reviews_url': CardReviewsResource(self).get_url(),
            'next_due_at_per_grade': dict((grade, rep.due_at)
                                          for (grade, rep)
                                          in self.obj.next_repetition_per_grade().items()),
        })

        return data

