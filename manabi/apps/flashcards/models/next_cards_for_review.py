from manabi.apps.flashcards.models import (
    Card,
)


class ReviewInterstitial(object):
    def __init__(self):
        from manabi.apps.flashcards.models.review_availabilities import (
            ReviewAvailabilities,
        )

        self.review_availabilities = ReviewAvailabilities()


class NextCardsForReview(object):
    def __init__(self, user, count, excluded_card_ids=set()):
        next_cards = Card.objects.next_cards(
            user,
            count,
            excluded_ids=excluded_card_ids,
            #TODO
        )
        # FIXME don't need 2 queries here...
        self.cards = Card.objects.filter(pk__in=[card.pk for card in next_cards])

        self.interstitial = ReviewInterstitial()
